/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Leaf-Spine Topology Simulation for TCP Congestion Control
 *
 * Topology:
 * - 2 ToR (Top-of-Rack) switches
 * - 2 Spine switches
 * - 16 servers per ToR (32 total servers)
 * - Server links: 100 Gbps
 * - Leaf-Spine links: 400 Gbps
 * - Propagation delay: 500 ns
 *
 * Traffic:
 * - Each server sends one 64MB flow to every other server
 * - Total: 32 * 31 = 992 flows
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/traffic-control-module.h"
#include "ns3/flow-monitor-module.h"

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <map>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("LeafSpineSimulation");

// Global variables for flow tracking
std::map<uint32_t, Time> flowStartTimes;
std::map<uint32_t, Time> flowCompletionTimes;
std::map<uint32_t, uint64_t> flowSizes;
std::ofstream fctFile;

// Flow size in bytes (64 MB)
const uint64_t FLOW_SIZE = 64 * 1024 * 1024;

// Buffer size at switches (based on typical datacenter switch design)
// For 100G ports: ~10-20 MB per port is typical
// For 400G ports: ~40-80 MB per port is typical
// We'll use moderate buffering: 10MB for 100G, 40MB for 400G
const uint32_t SERVER_BUFFER_SIZE = 10 * 1024 * 1024;  // 10 MB
const uint32_t SPINE_BUFFER_SIZE = 40 * 1024 * 1024;   // 40 MB

// Application completion callback
void
TxComplete (Ptr<OutputStreamWrapper> stream, Ptr<const Packet> packet)
{
  // This is called when a packet is transmitted
}

// Track flow completion
class FlowMonitor
{
public:
  static void
  InstallAll (NodeContainer servers)
  {
    m_servers = servers;
  }

  static void
  TrackFlow (uint32_t flowId, Ptr<Socket> socket, uint64_t flowSize)
  {
    flowStartTimes[flowId] = Simulator::Now ();
    flowSizes[flowId] = flowSize;

    // Schedule periodic checks for flow completion
    Simulator::Schedule (MilliSeconds (10), &FlowMonitor::CheckFlowCompletion, flowId, socket);
  }

  static void
  CheckFlowCompletion (uint32_t flowId, Ptr<Socket> socket)
  {
    if (flowCompletionTimes.find (flowId) != flowCompletionTimes.end ())
      {
        // Flow already completed
        return;
      }

    // Check if flow has sent all data
    // Note: In real implementation, we'd track bytes sent more accurately
    // For now, we'll check if socket is closed or simulation ended

    if (socket->GetTxAvailable () > 0)
      {
        // Still sending, check again later
        Simulator::Schedule (MilliSeconds (10), &FlowMonitor::CheckFlowCompletion, flowId, socket);
      }
    else
      {
        // Flow completed
        flowCompletionTimes[flowId] = Simulator::Now ();
        Time fct = flowCompletionTimes[flowId] - flowStartTimes[flowId];

        NS_LOG_INFO ("Flow " << flowId << " completed in " << fct.GetSeconds () << " seconds");
      }
  }

  static void
  PrintStatistics (std::string tcpVariant)
  {
    std::vector<double> fcts;

    for (auto const& entry : flowCompletionTimes)
      {
        uint32_t flowId = entry.first;
        Time completionTime = entry.second;
        Time startTime = flowStartTimes[flowId];
        Time fct = completionTime - startTime;

        fcts.push_back (fct.GetSeconds ());

        // Write to file
        fctFile << tcpVariant << "," << flowId << "," << fct.GetSeconds () << std::endl;
      }

    if (fcts.empty ())
      {
        NS_LOG_WARN ("No flows completed!");
        return;
      }

    // Calculate statistics
    std::sort (fcts.begin (), fcts.end ());

    double sum = 0;
    for (double fct : fcts)
      {
        sum += fct;
      }
    double avg = sum / fcts.size ();

    size_t p99_idx = (size_t)(fcts.size () * 0.99);
    double p99 = fcts[std::min (p99_idx, fcts.size () - 1)];

    std::cout << "\n=== Flow Completion Time Statistics for " << tcpVariant << " ===" << std::endl;
    std::cout << "Total flows: " << fcts.size () << std::endl;
    std::cout << "Average FCT: " << avg << " seconds" << std::endl;
    std::cout << "99th percentile FCT: " << p99 << " seconds" << std::endl;
    std::cout << "Min FCT: " << fcts[0] << " seconds" << std::endl;
    std::cout << "Max FCT: " << fcts[fcts.size () - 1] << " seconds" << std::endl;
  }

private:
  static NodeContainer m_servers;
};

NodeContainer FlowMonitor::m_servers;

// BulkSend application wrapper
class FlowApp
{
public:
  static uint32_t flowIdCounter;

  static void
  InstallFlow (Ptr<Node> srcNode, Ptr<Node> dstNode, uint16_t port, uint64_t maxBytes)
  {
    uint32_t flowId = flowIdCounter++;

    // Get destination address
    Ptr<Ipv4> ipv4 = dstNode->GetObject<Ipv4> ();
    Ipv4Address dstAddr = ipv4->GetAddress (1, 0).GetLocal ();

    // Create socket
    Ptr<Socket> socket = Socket::CreateSocket (srcNode, TcpSocketFactory::GetTypeId ());

    // Create BulkSendHelper
    BulkSendHelper source ("ns3::TcpSocketFactory",
                          InetSocketAddress (dstAddr, port));
    source.SetAttribute ("MaxBytes", UintegerValue (maxBytes));
    source.SetAttribute ("SendSize", UintegerValue (1024)); // 1 KB segments

    ApplicationContainer app = source.Install (srcNode);
    app.Start (Seconds (0.1));
    app.Stop (Seconds (100.0)); // Stop after 100 seconds

    // Install sink at destination
    PacketSinkHelper sink ("ns3::TcpSocketFactory",
                          InetSocketAddress (Ipv4Address::GetAny (), port));
    ApplicationContainer sinkApp = sink.Install (dstNode);
    sinkApp.Start (Seconds (0.0));
    sinkApp.Stop (Seconds (100.0));

    // Track flow
    FlowMonitor::TrackFlow (flowId, socket, maxBytes);
  }
};

uint32_t FlowApp::flowIdCounter = 0;

void
RunSimulation (std::string tcpVariant)
{
  NS_LOG_INFO ("Running simulation with TCP variant: " << tcpVariant);

  // Reset flow tracking
  flowStartTimes.clear ();
  flowCompletionTimes.clear ();
  flowSizes.clear ();
  FlowApp::flowIdCounter = 0;

  // Set TCP variant
  if (tcpVariant == "TcpNewReno")
    {
      Config::SetDefault ("ns3::TcpL4Protocol::SocketType", StringValue ("ns3::TcpNewReno"));
    }
  else if (tcpVariant == "TcpCubic")
    {
      Config::SetDefault ("ns3::TcpL4Protocol::SocketType", StringValue ("ns3::TcpCubic"));
    }
  else if (tcpVariant == "TcpMlCong")
    {
      Config::SetDefault ("ns3::TcpL4Protocol::SocketType", StringValue ("ns3::TcpMlCong"));
    }

  // TCP configuration
  Config::SetDefault ("ns3::TcpSocket::SegmentSize", UintegerValue (1448));
  Config::SetDefault ("ns3::TcpSocket::DelAckCount", UintegerValue (1));
  Config::SetDefault ("ns3::TcpSocket::InitialCwnd", UintegerValue (10));

  // Create nodes
  NS_LOG_INFO ("Creating nodes...");
  NodeContainer spineNodes;
  spineNodes.Create (2);

  NodeContainer torNodes;
  torNodes.Create (2);

  NodeContainer serverNodes;
  serverNodes.Create (32); // 16 per ToR

  // Install Internet stack
  InternetStackHelper internet;
  internet.Install (spineNodes);
  internet.Install (torNodes);
  internet.Install (serverNodes);

  // Create point-to-point helpers
  PointToPointHelper serverLink;
  serverLink.SetDeviceAttribute ("DataRate", StringValue ("100Gbps"));
  serverLink.SetChannelAttribute ("Delay", StringValue ("500ns"));
  serverLink.SetQueue ("ns3::DropTailQueue",
                      "MaxSize", StringValue (std::to_string (SERVER_BUFFER_SIZE) + "B"));

  PointToPointHelper spineLink;
  spineLink.SetDeviceAttribute ("DataRate", StringValue ("400Gbps"));
  spineLink.SetChannelAttribute ("Delay", StringValue ("500ns"));
  spineLink.SetQueue ("ns3::DropTailQueue",
                     "MaxSize", StringValue (std::to_string (SPINE_BUFFER_SIZE) + "B"));

  // Connect servers to ToRs
  NS_LOG_INFO ("Connecting servers to ToRs...");
  std::vector<NetDeviceContainer> serverToTorLinks;
  Ipv4AddressHelper ipv4;

  uint32_t subnetIndex = 1;
  for (uint32_t tor = 0; tor < 2; tor++)
    {
      for (uint32_t server = 0; server < 16; server++)
        {
          uint32_t serverIdx = tor * 16 + server;

          NetDeviceContainer link = serverLink.Install (serverNodes.Get (serverIdx),
                                                        torNodes.Get (tor));
          serverToTorLinks.push_back (link);

          // Assign IP addresses
          std::string subnet = "10." + std::to_string (subnetIndex / 256) + "." +
                              std::to_string (subnetIndex % 256) + ".0";
          ipv4.SetBase (subnet.c_str (), "255.255.255.0");
          ipv4.Assign (link);
          subnetIndex++;
        }
    }

  // Connect ToRs to Spines (full mesh)
  NS_LOG_INFO ("Connecting ToRs to Spines...");
  std::vector<NetDeviceContainer> torToSpineLinks;

  for (uint32_t tor = 0; tor < 2; tor++)
    {
      for (uint32_t spine = 0; spine < 2; spine++)
        {
          NetDeviceContainer link = spineLink.Install (torNodes.Get (tor),
                                                       spineNodes.Get (spine));
          torToSpineLinks.push_back (link);

          std::string subnet = "10." + std::to_string (subnetIndex / 256) + "." +
                              std::to_string (subnetIndex % 256) + ".0";
          ipv4.SetBase (subnet.c_str (), "255.255.255.0");
          ipv4.Assign (link);
          subnetIndex++;
        }
    }

  // Enable routing
  NS_LOG_INFO ("Setting up routing...");
  Ipv4GlobalRoutingHelper::PopulateRoutingTables ();

  // Install flow monitor
  FlowMonitor::InstallAll (serverNodes);

  // Create flows: each server sends to every other server
  NS_LOG_INFO ("Creating flows...");
  uint16_t basePort = 5000;

  for (uint32_t src = 0; src < 32; src++)
    {
      for (uint32_t dst = 0; dst < 32; dst++)
        {
          if (src != dst)
            {
              FlowApp::InstallFlow (serverNodes.Get (src),
                                   serverNodes.Get (dst),
                                   basePort + dst,
                                   FLOW_SIZE);
            }
        }
    }

  NS_LOG_INFO ("Starting simulation...");

  // Run simulation
  Simulator::Stop (Seconds (100.0));
  Simulator::Run ();

  // Print statistics
  FlowMonitor::PrintStatistics (tcpVariant);

  Simulator::Destroy ();

  NS_LOG_INFO ("Simulation completed for " << tcpVariant);
}

int
main (int argc, char *argv[])
{
  std::string tcpVariant = "TcpNewReno";
  bool runAll = false;

  CommandLine cmd;
  cmd.AddValue ("tcp", "TCP variant (TcpNewReno, TcpCubic, TcpMlCong)", tcpVariant);
  cmd.AddValue ("runAll", "Run all TCP variants", runAll);
  cmd.Parse (argc, argv);

  // Enable logging
  LogComponentEnable ("LeafSpineSimulation", LOG_LEVEL_INFO);

  // Open FCT output file
  fctFile.open ("flow_completion_times.csv");
  fctFile << "TcpVariant,FlowId,FCT(seconds)" << std::endl;

  if (runAll)
    {
      std::vector<std::string> variants = {"TcpNewReno", "TcpCubic", "TcpMlCong"};
      for (const auto& variant : variants)
        {
          std::cout << "\n\n========================================" << std::endl;
          std::cout << "Running with " << variant << std::endl;
          std::cout << "========================================\n" << std::endl;

          RunSimulation (variant);
        }
    }
  else
    {
      RunSimulation (tcpVariant);
    }

  fctFile.close ();

  std::cout << "\nResults written to flow_completion_times.csv" << std::endl;

  return 0;
}
