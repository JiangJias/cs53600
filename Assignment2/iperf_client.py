#!/usr/bin/env python3
"""
iPerf3-compatible TCP client implementation
Implements the iPerf3 protocol to communicate with standard iperf3 servers
"""

import socket
import json
import time
import struct
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import array

# Constants
IPERF_CONTROL_PORT = 5201
COOKIE_SIZE = 37
DEFAULT_DURATION = 60
SAMPLING_INTERVAL = 0.2  # 200ms
BUFFER_SIZE = 128 * 1024  # 128KB send buffer


@dataclass
class IperfResult:
    """Store results from iPerf test"""
    server_host: str
    server_port: int
    duration: float
    total_bytes: int
    avg_throughput: float
    throughput_samples: List[Tuple[float, float]]  # (timestamp, throughput_bps)
    tcp_stats: List[Dict]  # TCP statistics samples
    success: bool
    error_msg: Optional[str] = None


class IperfClient:
    """iPerf3 compatible TCP client"""

    def __init__(self, server_host: str, server_port: int = IPERF_CONTROL_PORT,
                 duration: int = DEFAULT_DURATION, sampling_interval: float = SAMPLING_INTERVAL):
        self.server_host = server_host
        self.server_port = server_port
        self.duration = duration
        self.sampling_interval = sampling_interval
        self.control_sock = None
        self.data_sock = None
        self.cookie = None
        self.logger = logging.getLogger(f"IperfClient[{server_host}]")

    # Assignment 2
    # def _create_socket(self, timeout: int = 10) -> socket.socket:
    #     """Create a TCP socket with timeout"""
    #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    #     sock.settimeout(timeout)
    #     return sock

    # Assignment 3
    def _create_socket(self, timeout: int = 15, cc_algo: str = 'mlcc') -> socket.socket:
        """
        Create a TCP socket and optionally set a specific congestion control algorithm.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        # Core bonus requirement: Select the congestion control algorithm in the socket application
        try:
            # TCP_CONGESTION is typically defined as 13 in <netinet/tcp.h> on Linux
            TCP_CONGESTION = getattr(socket, 'TCP_CONGESTION', 13)
            # sock.setsockopt(socket.IPPROTO_TCP, TCP_CONGESTION, b'cubic')
            # sock.setsockopt(socket.IPPROTO_TCP, TCP_CONGESTION, b'reno')
            sock.setsockopt(socket.IPPROTO_TCP, TCP_CONGESTION, cc_algo.encode())
            self.logger.info(f"Successfully set TCP Congestion Control to: {cc_algo}")
        except Exception as e:
            self.logger.warning(f"Could not set CC algorithm to {cc_algo}. Ensure you are on Linux/WSL. Error: {e}")

        sock.settimeout(timeout)
        return sock

    def _send_json(self, sock: socket.socket, data: Dict) -> bool:
        """Send JSON message with length prefix (iPerf3 protocol)"""
        try:
            json_str = json.dumps(data)
            json_bytes = json_str.encode('utf-8')
            # iPerf3 uses 4-byte length prefix in network byte order
            length = struct.pack('!I', len(json_bytes))
            sock.sendall(length + json_bytes)
            return True
        except Exception as e:
            self.logger.error(f"Failed to send JSON: {e}")
            return False

    def _recv_json(self, sock: socket.socket) -> Optional[Dict]:
        """Receive JSON message with length prefix"""
        try:
            # Read 4-byte length prefix
            length_data = self._recv_exact(sock, 4)
            if not length_data or len(length_data) != 4:
                self.logger.debug(f"Failed to receive length prefix (got {len(length_data) if length_data else 0} bytes)")
                return None

            length = struct.unpack('!I', length_data)[0]

            # Sanity check on length
            if length == 0 or length > 1000000:  # Max 1MB
                self.logger.error(f"Invalid JSON length: {length}")
                return None

            # Read JSON data
            json_bytes = self._recv_exact(sock, length)
            if not json_bytes or len(json_bytes) != length:
                self.logger.debug(f"Failed to receive JSON data (expected {length}, got {len(json_bytes) if json_bytes else 0} bytes)")
                return None

            json_str = json_bytes.decode('utf-8')
            return json.loads(json_str)
        except socket.timeout:
            self.logger.error(f"Timeout while receiving JSON")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to receive JSON: {e}")
            return None

    def _recv_exact(self, sock: socket.socket, size: int) -> Optional[bytes]:
        """Receive exactly size bytes from socket"""
        data = b''
        while len(data) < size:
            try:
                chunk = sock.recv(size - len(data))
                if not chunk:
                    self.logger.debug(f"Connection closed while receiving (got {len(data)}/{size} bytes)")
                    return None
                data += chunk
            except socket.timeout:
                self.logger.debug(f"Timeout while receiving (got {len(data)}/{size} bytes)")
                return None
            except socket.error as e:
                self.logger.debug(f"Socket error while receiving: {e}")
                return None
        return data

    def _establish_control_connection(self) -> bool:
        """Establish control connection with iPerf3 server"""
        try:
            self.control_sock = self._create_socket(timeout=15)
            self.logger.info(f"Connecting to {self.server_host}:{self.server_port}")
            self.control_sock.connect((self.server_host, self.server_port))
            self.logger.info("Control connection established")
            return True
        except socket.timeout:
            self.logger.error(f"Connection timeout to {self.server_host}:{self.server_port}")
            return False
        except ConnectionRefusedError:
            self.logger.error(f"Connection refused by {self.server_host}:{self.server_port}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to establish control connection: {e}")
            return False

    def _exchange_parameters(self) -> bool:
        """Exchange test parameters with iPerf3 server (skip greeting, send directly)"""
        try:
            # Set a reasonable timeout for parameter exchange
            original_timeout = self.control_sock.gettimeout()
            self.control_sock.settimeout(10)

            # Skip waiting for server greeting - directly send client parameters
            # Some servers don't send greeting or expect client to send first
            self.logger.debug("Skipping server greeting, sending parameters directly...")

            # Send client parameters immediately
            client_params = {
                'tcp': True,
                'omit': 0,
                'time': self.duration,
                'parallel': 1,
                'len': BUFFER_SIZE,
                'client_version': '3.9',
            }

            if not self._send_json(self.control_sock, client_params):
                return False

            self.logger.info("Parameters sent to server")

            # Try to receive server response (may include cookie)
            response = self._recv_json(self.control_sock)
            if response:
                self.logger.debug(f"Server response: {response}")

                # Extract cookie if present
                self.cookie = response.get('cookie')

                # Check for errors
                if 'error' in response:
                    self.logger.error(f"Server error: {response['error']}")
                    return False
            else:
                # Some servers may not respond with JSON, just continue
                self.logger.warning("No JSON response from server, will attempt to continue")
                # Generate a simple cookie for identification
                self.cookie = f"client_{int(time.time())}"

            # Restore original timeout
            self.control_sock.settimeout(original_timeout)
            return True

        except socket.timeout:
            self.logger.error("Timeout during parameter exchange")
            return False
        except Exception as e:
            self.logger.error(f"Parameter exchange failed: {e}")
            return False

    def _get_tcp_info(self, sock: socket.socket) -> Dict:
        """Extract TCP_INFO statistics from socket"""
        tcp_info = {}
        try:
            # Get TCP_INFO on Linux
            if hasattr(socket, 'TCP_INFO'):
                fmt = "B" * 7 + "I" * 21
                tcp_info_struct = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, 104)
                tcp_info_tuple = struct.unpack(fmt, tcp_info_struct)

                # Parse relevant fields (Linux TCP_INFO structure)
                tcp_info = {
                    'state': tcp_info_tuple[0],
                    'ca_state': tcp_info_tuple[1],
                    'retransmits': tcp_info_tuple[2],
                    'rto': tcp_info_tuple[7],
                    'ato': tcp_info_tuple[8],
                    'snd_mss': tcp_info_tuple[9],
                    'rcv_mss': tcp_info_tuple[10],
                    'unacked': tcp_info_tuple[11],
                    'sacked': tcp_info_tuple[12],
                    'lost': tcp_info_tuple[13],
                    'retrans': tcp_info_tuple[14],
                    'fackets': tcp_info_tuple[15],
                    'last_data_sent': tcp_info_tuple[16],
                    'last_ack_sent': tcp_info_tuple[17],
                    'last_data_recv': tcp_info_tuple[18],
                    'last_ack_recv': tcp_info_tuple[19],
                    'pmtu': tcp_info_tuple[20],
                    'rcv_ssthresh': tcp_info_tuple[21],
                    'rtt': tcp_info_tuple[22],  # in microseconds
                    'rttvar': tcp_info_tuple[23],
                    'snd_ssthresh': tcp_info_tuple[24],
                    'snd_cwnd': tcp_info_tuple[25],
                    'advmss': tcp_info_tuple[26],
                    'reordering': tcp_info_tuple[27],
                }
        except (OSError, AttributeError, struct.error) as e:
            self.logger.debug(f"Could not get TCP_INFO: {e}")

        # Get bytes sent/received
        try:
            if hasattr(socket, 'SO_MEMINFO'):
                tcp_info['so_meminfo'] = sock.getsockopt(socket.SOL_SOCKET, socket.SO_MEMINFO)
        except (OSError, AttributeError):
            pass

        return tcp_info

    def _open_data_connection(self) -> bool:
        """Open data connection for sending data"""
        try:
            # Try to wait for server start message (optional - use short timeout)
            self.control_sock.settimeout(2)
            start_msg = self._recv_json(self.control_sock)
            if start_msg:
                self.logger.debug(f"Start message: {start_msg}")
            else:
                # No start message - proceed anyway
                self.logger.debug("No start message from server, proceeding to create data connection")

            # Create data connection
            self.data_sock = self._create_socket(timeout=30)
            self.data_sock.connect((self.server_host, self.server_port))

            # Send cookie to identify this test (if we have one)
            if self.cookie:
                try:
                    cookie_bytes = self.cookie.encode('utf-8')
                    self.data_sock.sendall(cookie_bytes)
                    self.logger.debug(f"Sent cookie: {self.cookie}")
                except Exception as e:
                    self.logger.warning(f"Could not send cookie: {e}, continuing anyway")

            self.logger.info("Data connection established")
            return True
        except socket.timeout:
            # Timeout on start message is OK - try to continue
            self.logger.debug("Timeout waiting for start message, attempting direct connection")
            try:
                # Create data connection anyway
                self.data_sock = self._create_socket(timeout=30)
                self.data_sock.connect((self.server_host, self.server_port))
                self.logger.info("Data connection established (no start message)")
                return True
            except Exception as e:
                self.logger.error(f"Failed to open data connection: {e}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to open data connection: {e}")
            return False

    def _send_data(self) -> Tuple[List[Tuple[float, float]], List[Dict]]:
        """Send data and collect throughput samples"""
        throughput_samples = []
        tcp_stats = []

        send_buffer = b'0' * BUFFER_SIZE
        start_time = time.time()
        last_sample_time = start_time
        bytes_in_interval = 0
        total_bytes_sent = 0
        last_tcp_info = None

        try:
            self.logger.info(f"Starting data transfer for {self.duration} seconds")

            while time.time() - start_time < self.duration:
                try:
                    # Send data
                    sent = self.data_sock.send(send_buffer)
                    bytes_in_interval += sent
                    total_bytes_sent += sent

                    current_time = time.time()
                    elapsed_in_interval = current_time - last_sample_time

                    # Sample at regular intervals
                    if elapsed_in_interval >= self.sampling_interval:
                        # Calculate throughput in bps
                        throughput_bps = (bytes_in_interval * 8) / elapsed_in_interval
                        timestamp = current_time - start_time
                        throughput_samples.append((timestamp, throughput_bps))

                        # Get TCP stats
                        tcp_info = self._get_tcp_info(self.data_sock)
                        tcp_info['timestamp'] = timestamp
                        tcp_info['throughput_bps'] = throughput_bps
                        tcp_info['bytes_sent'] = total_bytes_sent

                        # Calculate bytes acked (approximately)
                        if last_tcp_info:
                            tcp_info['bytes_acked_interval'] = bytes_in_interval

                        tcp_stats.append(tcp_info)
                        last_tcp_info = tcp_info

                        self.logger.debug(f"t={timestamp:.2f}s, throughput={throughput_bps/1e6:.2f} Mbps, "
                                        f"cwnd={tcp_info.get('snd_cwnd', 'N/A')}, "
                                        f"rtt={tcp_info.get('rtt', 'N/A')}us")

                        # Reset for next interval
                        bytes_in_interval = 0
                        last_sample_time = current_time

                except socket.timeout:
                    self.logger.warning("Socket timeout during send")
                    break
                except socket.error as e:
                    self.logger.error(f"Socket error during send: {e}")
                    break

            self.logger.info(f"Data transfer completed. Total bytes sent: {total_bytes_sent}")

        except Exception as e:
            self.logger.error(f"Error during data transfer: {e}")

        return throughput_samples, tcp_stats

    def _cleanup(self):
        """Close connections"""
        if self.data_sock:
            try:
                self.data_sock.close()
            except:
                pass

        if self.control_sock:
            try:
                # Try to receive final results from server
                final_result = self._recv_json(self.control_sock)
                if final_result:
                    self.logger.debug(f"Final result from server: {final_result}")
                self.control_sock.close()
            except:
                pass

    def run_test(self) -> IperfResult:
        """Run complete iPerf test"""
        self.logger.info(f"Starting iPerf test to {self.server_host}:{self.server_port}")

        try:
            # Establish control connection
            if not self._establish_control_connection():
                return IperfResult(
                    server_host=self.server_host,
                    server_port=self.server_port,
                    duration=0,
                    total_bytes=0,
                    avg_throughput=0,
                    throughput_samples=[],
                    tcp_stats=[],
                    success=False,
                    error_msg="Failed to establish control connection"
                )

            # Exchange parameters
            if not self._exchange_parameters():
                self._cleanup()
                return IperfResult(
                    server_host=self.server_host,
                    server_port=self.server_port,
                    duration=0,
                    total_bytes=0,
                    avg_throughput=0,
                    throughput_samples=[],
                    tcp_stats=[],
                    success=False,
                    error_msg="Parameter exchange failed"
                )

            # Open data connection
            if not self._open_data_connection():
                self._cleanup()
                return IperfResult(
                    server_host=self.server_host,
                    server_port=self.server_port,
                    duration=0,
                    total_bytes=0,
                    avg_throughput=0,
                    throughput_samples=[],
                    tcp_stats=[],
                    success=False,
                    error_msg="Failed to open data connection"
                )

            # Send data and collect samples
            throughput_samples, tcp_stats = self._send_data()

            # Calculate statistics
            total_bytes = sum(sample[1] / 8 * self.sampling_interval for sample in throughput_samples)
            avg_throughput = sum(sample[1] for sample in throughput_samples) / len(throughput_samples) if throughput_samples else 0

            self.logger.info(f"Test completed successfully. Avg throughput: {avg_throughput/1e6:.2f} Mbps")

            return IperfResult(
                server_host=self.server_host,
                server_port=self.server_port,
                duration=self.duration,
                total_bytes=int(total_bytes),
                avg_throughput=avg_throughput,
                throughput_samples=throughput_samples,
                tcp_stats=tcp_stats,
                success=True
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {e}")
            return IperfResult(
                server_host=self.server_host,
                server_port=self.server_port,
                duration=0,
                total_bytes=0,
                avg_throughput=0,
                throughput_samples=[],
                tcp_stats=[],
                success=False,
                error_msg=str(e)
            )
        finally:
            self._cleanup()


def test_client(host: str, port: int = IPERF_CONTROL_PORT, duration: int = 10):
    """Test function to run a single iPerf test"""
    logging.basicConfig(level=logging.INFO)
    client = IperfClient(host, port, duration)
    result = client.run_test()

    if result.success:
        print(f"Test successful!")
        print(f"Duration: {result.duration}s")
        print(f"Total bytes: {result.total_bytes}")
        print(f"Avg throughput: {result.avg_throughput/1e6:.2f} Mbps")
        print(f"Samples collected: {len(result.throughput_samples)}")
    else:
        print(f"Test failed: {result.error_msg}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_client(sys.argv[1])
    else:
        print("Usage: python iperf_client.py <server_host>")
