import os
import time
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
import matplotlib.pyplot as plt

# ==========================================
# 1. AllGather Implementations
# ==========================================
def allgather_ring(rank, world_size, local_tensor):
    """Ring AllGather: Unidirectional passing in a circle."""
    result = [torch.zeros_like(local_tensor) for _ in range(world_size)]
    result[rank] = local_tensor.clone()
    send_chunk = local_tensor.clone()
    recv_buffer = torch.zeros_like(local_tensor)
    
    left = (rank - 1) % world_size
    right = (rank + 1) % world_size

    for step in range(1, world_size):
        recv_chunk_idx = (rank - step) % world_size
        if rank % 2 == 0:
            dist.send(tensor=send_chunk, dst=right)
            dist.recv(tensor=recv_buffer, src=left)
        else:
            dist.recv(tensor=recv_buffer, src=left)
            dist.send(tensor=send_chunk, dst=right)
        result[recv_chunk_idx] = recv_buffer.clone()
        send_chunk = recv_buffer.clone()
    return result

def allgather_recursive_doubling(rank, world_size, local_tensor):
    """Recursive Doubling AllGather: Pairs exchange data at distance 2^k."""
    result = [torch.zeros_like(local_tensor) for _ in range(world_size)]
    result[rank] = local_tensor.clone()
    
    if not (world_size > 0 and ((world_size & (world_size - 1)) == 0)):
        # Fallback to Ring if not a power of 2 to avoid crashes in tests
        return allgather_ring(rank, world_size, local_tensor)

    current_chunks = [rank]
    step = 0
    while (1 << step) < world_size:
        distance = 1 << step
        partner = rank ^ distance
        
        send_data = torch.cat([result[idx] for idx in current_chunks])
        recv_data = torch.zeros_like(send_data)
        
        if rank < partner:
            dist.send(tensor=send_data, dst=partner)
            dist.recv(tensor=recv_data, src=partner)
        else:
            dist.recv(tensor=recv_data, src=partner)
            dist.send(tensor=send_data, dst=partner)
            
        partner_chunks = [c ^ distance for c in current_chunks]
        recv_chunks = recv_data.view(len(partner_chunks), *local_tensor.shape)
        
        for i, p_idx in enumerate(partner_chunks):
            result[p_idx] = recv_chunks[i].clone()
            
        current_chunks.extend(partner_chunks)
        current_chunks.sort()
        step += 1
    return result

def allgather_swing(rank, world_size, local_tensor):
    """Swing AllGather: Simplified bidirectional ring to overlap communication."""
    result = [torch.zeros_like(local_tensor) for _ in range(world_size)]
    result[rank] = local_tensor.clone()
    
    send_right = local_tensor.clone()
    send_left = local_tensor.clone()
    recv_right = torch.zeros_like(local_tensor)
    recv_left = torch.zeros_like(local_tensor)
    
    left_neighbor = (rank - 1) % world_size
    right_neighbor = (rank + 1) % world_size

    # Needs approx half the steps since data flows both ways
    steps = world_size // 2
    for step in range(1, steps + 1):
        idx_from_left = (rank - step) % world_size
        idx_from_right = (rank + step) % world_size

        if rank % 2 == 0:
            dist.send(tensor=send_right, dst=right_neighbor)
            dist.recv(tensor=recv_left, src=left_neighbor)
            dist.send(tensor=send_left, dst=left_neighbor)
            dist.recv(tensor=recv_right, src=right_neighbor)
        else:
            dist.recv(tensor=recv_left, src=left_neighbor)
            dist.send(tensor=send_right, dst=right_neighbor)
            dist.recv(tensor=recv_right, src=right_neighbor)
            dist.send(tensor=send_left, dst=left_neighbor)

        result[idx_from_left] = recv_left.clone()
        result[idx_from_right] = recv_right.clone()
        send_right = recv_left.clone()
        send_left = recv_right.clone()

    return result

# ==========================================
# 2. Broadcast Implementations
# ==========================================
def broadcast_binary_tree(rank, world_size, local_tensor, root=0):
    """Binary Tree Broadcast: Node i sends to 2i+1 and 2i+2."""
    left_child = 2 * rank + 1
    right_child = 2 * rank + 2
    parent = (rank - 1) // 2

    # Receive from parent if not root
    if rank != root:
        dist.recv(tensor=local_tensor, src=parent)

    # Send to children if they exist
    if left_child < world_size:
        dist.send(tensor=local_tensor, dst=left_child)
    if right_child < world_size:
        dist.send(tensor=local_tensor, dst=right_child)
        
    return local_tensor

def broadcast_binomial_tree(rank, world_size, local_tensor, root=0):
    """Binomial Tree Broadcast: Number of senders doubles every step O(log N)."""
    step = 1
    while step < world_size:
        # If I already have the data, I am a sender
        if rank < step:
            target = rank + step
            if target < world_size:
                dist.send(tensor=local_tensor, dst=target)
        # If it's my turn to receive the data
        elif rank >= step and rank < step * 2:
            source = rank - step
            dist.recv(tensor=local_tensor, src=source)
            
        step *= 2
    return local_tensor

# ==========================================
# 3. Distributed Worker Process
# ==========================================
def worker_fn(rank, world_size, test_cases, return_dict):
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '12345'
    dist.init_process_group("gloo", rank=rank, world_size=world_size)
    
    results = []
    
    for size_bytes in test_cases:
        num_elements = size_bytes // 4
        
        # We need distinct tensors for AllGather and Broadcast
        ag_tensor = torch.ones(num_elements, dtype=torch.float32) * rank
        
        # For broadcast, only rank 0 has the actual data initially
        bc_tensor = torch.ones(num_elements, dtype=torch.float32) * 99 if rank == 0 else torch.zeros(num_elements, dtype=torch.float32)
        
        dist.barrier()
        
        # 1. Ring AllGather
        start = time.perf_counter()
        _ = allgather_ring(rank, world_size, ag_tensor)
        dist.barrier()
        t_ring = time.perf_counter() - start
        
        # 2. Recursive Doubling AllGather
        start = time.perf_counter()
        _ = allgather_recursive_doubling(rank, world_size, ag_tensor)
        dist.barrier()
        t_rd = time.perf_counter() - start

        # 3. Swing AllGather
        start = time.perf_counter()
        _ = allgather_swing(rank, world_size, ag_tensor)
        dist.barrier()
        t_swing = time.perf_counter() - start

        # 4. Binary Tree Broadcast
        start = time.perf_counter()
        _ = broadcast_binary_tree(rank, world_size, bc_tensor.clone(), root=0)
        dist.barrier()
        t_binary = time.perf_counter() - start

        # 5. Binomial Tree Broadcast
        start = time.perf_counter()
        _ = broadcast_binomial_tree(rank, world_size, bc_tensor.clone(), root=0)
        dist.barrier()
        t_binomial = time.perf_counter() - start

        if rank == 0:
            results.append((t_ring, t_rd, t_swing, t_binary, t_binomial))
            
    dist.destroy_process_group()
    if rank == 0:
        return_dict[world_size] = results

# ==========================================
# 4. Experiment Scheduling and Plotting Logic
# ==========================================
def run_experiments():
    print("Starting Comprehensive Benchmarks...")
    manager = mp.Manager()
    
    # --- Experiment 1: Varying Message Size (Fixed Ranks = 4) ---
    print("\nRunning Varying Message Size (Ranks=4)...")
    world_size = 4
    sizes_kb = [1, 4, 16, 64, 256, 1024, 4096, 16384] 
    sizes_bytes = [s * 1024 for s in sizes_kb]
    
    return_dict_size = manager.dict()
    mp.spawn(worker_fn, args=(world_size, sizes_bytes, return_dict_size), nprocs=world_size, join=True)
    
    times_size = return_dict_size[world_size]
    
    # Plot AllGather (Size)
    plt.figure(figsize=(8, 5))
    plt.plot(sizes_kb, [t[0] for t in times_size], marker='o', label='Ring')
    plt.plot(sizes_kb, [t[1] for t in times_size], marker='s', label='Recursive Doubling')
    plt.plot(sizes_kb, [t[2] for t in times_size], marker='^', label='Swing')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Message Size (KB)')
    plt.ylabel('Completion Time (Seconds)')
    plt.title('AllGather: Varying Message Size (4 Ranks)')
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.savefig('allgather_msg_size.png')

    # Plot Broadcast (Size)
    plt.figure(figsize=(8, 5))
    plt.plot(sizes_kb, [t[3] for t in times_size], marker='x', label='Binary Tree')
    plt.plot(sizes_kb, [t[4] for t in times_size], marker='d', label='Binomial Tree')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Message Size (KB)')
    plt.ylabel('Completion Time (Seconds)')
    plt.title('Broadcast: Varying Message Size (4 Ranks)')
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.savefig('broadcast_msg_size.png')

    # --- Experiment 2: Varying Ranks (Fixed Size = 1MB) ---
    print("\nRunning Varying Ranks (Size=1MB)...")
    fixed_size_bytes = [1024 * 1024]
    ranks_to_test = [2, 4, 8] # Sticking to powers of 2 for clean topologies
    
    return_dict_ranks = manager.dict()
    for w_size in ranks_to_test:
        print(f"Testing with {w_size} Ranks...")
        mp.spawn(worker_fn, args=(w_size, fixed_size_bytes, return_dict_ranks), nprocs=w_size, join=True)
        
    # Extract data across ranks
    ring_r = [return_dict_ranks[w][0][0] for w in ranks_to_test]
    rd_r = [return_dict_ranks[w][0][1] for w in ranks_to_test]
    swing_r = [return_dict_ranks[w][0][2] for w in ranks_to_test]
    binary_r = [return_dict_ranks[w][0][3] for w in ranks_to_test]
    binomial_r = [return_dict_ranks[w][0][4] for w in ranks_to_test]

    # Plot AllGather (Ranks)
    plt.figure(figsize=(8, 5))
    plt.plot(ranks_to_test, ring_r, marker='o', label='Ring')
    plt.plot(ranks_to_test, rd_r, marker='s', label='Recursive Doubling')
    plt.plot(ranks_to_test, swing_r, marker='^', label='Swing')
    plt.xlabel('Number of Ranks')
    plt.ylabel('Completion Time (Seconds)')
    plt.title('AllGather: Varying Ranks (1MB Message)')
    plt.grid(True, linestyle='--')
    plt.legend()
    plt.savefig('allgather_ranks.png')

    # Plot Broadcast (Ranks)
    plt.figure(figsize=(8, 5))
    plt.plot(ranks_to_test, binary_r, marker='x', label='Binary Tree')
    plt.plot(ranks_to_test, binomial_r, marker='d', label='Binomial Tree')
    plt.xlabel('Number of Ranks')
    plt.ylabel('Completion Time (Seconds)')
    plt.title('Broadcast: Varying Ranks (1MB Message)')
    plt.grid(True, linestyle='--')
    plt.legend()
    plt.savefig('broadcast_ranks.png')

    print("\nAll experiments completed successfully! 4 charts have been saved.")

if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    run_experiments()