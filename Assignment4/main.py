import gurobipy as gp
from gurobipy import GRB

def solve_hose_network_design():
    # Define parameters based on assignment requirements
    n = 8
    d = 4

    try:
        # 1. Create the model
        model = gp.Model("Hose_Model_Network_Design")

        # ==========================================
        # 2. Decision Variables
        # ==========================================
        # Topology variables: x[i,j] = 1 indicates a physical link from node i to node j
        x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
        
        # Routing variables: f[i,j,s,dst] represents the fraction of traffic from s to dst routed over link i->j
        f = model.addVars(n, n, n, n, lb=0.0, ub=1.0, name="f")
        
        # Dual variables: to handle the infinite traffic matrices in the Hose model
        alpha = model.addVars(n, n, n, lb=0.0, name="alpha") # Corresponds to source capacity constraints
        beta = model.addVars(n, n, n, lb=0.0, name="beta")   # Corresponds to destination capacity constraints
        
        # Maximum link utilization (U = 1 / concurrent_flow)
        U = model.addVar(lb=0.0, name="U")

        # ==========================================
        # 3. Objective Function
        # ==========================================
        # Minimize the maximum link utilization, which is equivalent to maximizing the concurrent flow (λ)
        model.setObjective(U, GRB.MINIMIZE)

        # ==========================================
        # 4. Constraints
        # ==========================================
        
        # Constraint 4.1: Topology degree constraints
        for i in range(n):
            # No self-loops allowed
            model.addConstr(x[i, i] == 0, name=f"no_self_loop_{i}")
            # Each node has exactly 'd' outgoing and 'd' incoming links
            model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == d, name=f"out_degree_{i}")
            model.addConstr(gp.quicksum(x[j, i] for j in range(n)) == d, name=f"in_degree_{i}")

        # Constraint 4.2: Routing and Capacity Control
        for s in range(n):
            for dst in range(n):
                if s == dst:
                    continue
                
                # 4.2.a: Flow conservation constraints
                for i in range(n):
                    out_flow = gp.quicksum(f[i, j, s, dst] for j in range(n))
                    in_flow = gp.quicksum(f[j, i, s, dst] for j in range(n))
                    
                    if i == s:
                        model.addConstr(out_flow - in_flow == 1, name=f"flow_cons_src_{s}_{dst}_{i}")
                    elif i == dst:
                        model.addConstr(out_flow - in_flow == -1, name=f"flow_cons_dst_{s}_{dst}_{i}")
                    else:
                        model.addConstr(out_flow - in_flow == 0, name=f"flow_cons_transit_{s}_{dst}_{i}")

                # 4.2.b: Dual constraints and physical link limitations
                for i in range(n):
                    for j in range(n):
                        # Traffic fraction can only exist if the physical link exists
                        model.addConstr(f[i, j, s, dst] <= x[i, j], name=f"link_exist_{i}_{j}_{s}_{dst}")
                        
                        # Hose dual constraints (derived from LP duality)
                        model.addConstr(alpha[i, j, s] + beta[i, j, dst] >= f[i, j, s, dst], 
                                        name=f"hose_dual_{i}_{j}_{s}_{dst}")

        # Constraint 4.3: Maximum Utilization Boundary Limits
        # For each link i->j, under any valid traffic matrix, total traffic must be <= U * capacity(1)
        for i in range(n):
            for j in range(n):
                # 4 is the max volume per node defined in T_hose
                worst_case_traffic = 4 * gp.quicksum(alpha[i, j, s] for s in range(n)) + \
                                     4 * gp.quicksum(beta[i, j, dst] for dst in range(n))
                
                # Ensure the worst-case traffic does not exceed our tracked max utilization U
                model.addConstr(worst_case_traffic <= U, name=f"max_util_{i}_{j}")

        # ==========================================
        # 5. Optimization and Output
        # ==========================================
        # Set Gurobi parameters to speed up solving for highly symmetric graph problems
        model.setParam('MIPFocus', 1) 
        model.setParam('TimeLimit', 600)
        model.setParam('MIPGap', 0.02)
        model.optimize()

        if model.status == GRB.OPTIMAL:
            max_concurrent_flow = 1.0 / U.X
            print("\n" + "="*50)
            print("🚀 Optimal solution found!")
            print("="*50)
            print(f"Min-Max Utilization (U): {U.X:.4f}")
            print(f"Maximum Concurrent Flow (λ): {max_concurrent_flow:.4f}")
            
            print("\nOptimal Topology (Adjacency Matrix):")
            print("    " + "  ".join(f"N{i}" for i in range(n)))
            for i in range(n):
                row = []
                for j in range(n):
                    # Handle floating-point precision issues natively in Gurobi results
                    val = 1 if x[i, j].X > 0.5 else 0
                    row.append(str(val))
                print(f"N{i} [{', '.join(row)}]")
        else:
            print(f"Failed to find optimal solution. Model status code: {model.status}")

    except gp.GurobiError as e:
        print(f"Gurobi Error: {e}")

if __name__ == "__main__":
    solve_hose_network_design()