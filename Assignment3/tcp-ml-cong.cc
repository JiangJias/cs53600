/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2026
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 */

#include "tcp-ml-cong.h"
#include "ns3/log.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("TcpMlCong");
NS_OBJECT_ENSURE_REGISTERED (TcpMlCong);

TypeId
TcpMlCong::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::TcpMlCong")
    .SetParent<TcpNewReno> ()
    .SetGroupName ("Internet")
    .AddConstructor<TcpMlCong> ()
    .AddAttribute ("Alpha",
                   "RTT penalty weight in objective function",
                   DoubleValue (1.0),
                   MakeDoubleAccessor (&TcpMlCong::m_alpha),
                   MakeDoubleChecker<double> ())
    .AddAttribute ("Beta",
                   "Loss penalty weight in objective function",
                   DoubleValue (1.0),
                   MakeDoubleAccessor (&TcpMlCong::m_beta),
                   MakeDoubleChecker<double> ())
    .AddAttribute ("RttThreshold",
                   "RTT increase threshold as fraction of baseline (e.g., 0.2 = 20%)",
                   DoubleValue (0.2),
                   MakeDoubleAccessor (&TcpMlCong::m_rttThreshold),
                   MakeDoubleChecker<double> ())
  ;
  return tid;
}

TcpMlCong::TcpMlCong (void)
  : TcpNewReno (),
    m_minRtt (Time::Max ()),
    m_baseRtt (Time::Max ()),
    m_alpha (1.0),
    m_beta (1.0),
    m_consecutiveIncrements (0),
    m_lastCwnd (0),
    m_lastRtt (Time::Max ()),
    m_rttThreshold (0.2),
    m_inCongestionAvoidance (false)
{
  NS_LOG_FUNCTION (this);
}

TcpMlCong::TcpMlCong (const TcpMlCong& sock)
  : TcpNewReno (sock),
    m_minRtt (sock.m_minRtt),
    m_baseRtt (sock.m_baseRtt),
    m_alpha (sock.m_alpha),
    m_beta (sock.m_beta),
    m_consecutiveIncrements (sock.m_consecutiveIncrements),
    m_lastCwnd (sock.m_lastCwnd),
    m_lastRtt (sock.m_lastRtt),
    m_rttThreshold (sock.m_rttThreshold),
    m_inCongestionAvoidance (sock.m_inCongestionAvoidance)
{
  NS_LOG_FUNCTION (this);
}

TcpMlCong::~TcpMlCong (void)
{
  NS_LOG_FUNCTION (this);
}

Ptr<TcpCongestionOps>
TcpMlCong::Fork (void)
{
  return CopyObject<TcpMlCong> (this);
}

std::string
TcpMlCong::GetName () const
{
  return "TcpMlCong";
}

void
TcpMlCong::PktsAcked (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked, const Time& rtt)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked << rtt);

  if (rtt.IsZero ())
    {
      return;
    }

  // Update minimum RTT (baseline)
  if (rtt < m_minRtt)
    {
      m_minRtt = rtt;
      if (m_baseRtt == Time::Max ())
        {
          m_baseRtt = rtt;
        }
    }

  // Update baseline RTT with slow adaptation
  if (rtt < m_baseRtt)
    {
      m_baseRtt = rtt;
    }

  m_lastRtt = rtt;
}

bool
TcpMlCong::ShouldSlowDown (Time currentRtt)
{
  NS_LOG_FUNCTION (this << currentRtt);

  if (m_baseRtt == Time::Max () || currentRtt.IsZero ())
    {
      return false;
    }

  // Check if RTT has increased significantly (more than threshold)
  double rttIncrease = (currentRtt.GetSeconds () - m_baseRtt.GetSeconds ()) / m_baseRtt.GetSeconds ();

  if (rttIncrease > m_rttThreshold)
    {
      NS_LOG_DEBUG ("RTT increase detected: " << rttIncrease * 100 << "% - slowing down");
      return true;
    }

  return false;
}

uint32_t
TcpMlCong::CalculateIncrease (Ptr<TcpSocketState> tcb)
{
  NS_LOG_FUNCTION (this << tcb);

  uint32_t segCwnd = tcb->m_cWnd / tcb->m_segmentSize;

  // Base increase: 1 MSS per RTT (standard AIMD)
  uint32_t baseIncrease = tcb->m_segmentSize;

  // Adjust based on RTT conditions
  if (ShouldSlowDown (m_lastRtt))
    {
      // Be more conservative: slow down growth by 50%
      return baseIncrease / 2;
    }

  // Check if cwnd has been stable (not growing)
  if (tcb->m_cWnd == m_lastCwnd)
    {
      m_consecutiveIncrements = 0;
    }
  else if (tcb->m_cWnd > m_lastCwnd)
    {
      m_consecutiveIncrements++;
    }

  // If we've been increasing for a while but RTT is stable, be slightly more aggressive
  if (m_consecutiveIncrements > 5 && !ShouldSlowDown (m_lastRtt))
    {
      // Slightly faster growth: 1.5 MSS per RTT
      return (baseIncrease * 3) / 2;
    }

  return baseIncrease;
}

void
TcpMlCong::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);

  m_lastCwnd = tcb->m_cWnd;

  if (tcb->m_cWnd < tcb->m_ssThresh)
    {
      // Slow start: exponential increase
      m_inCongestionAvoidance = false;
      tcb->m_cWnd += tcb->m_segmentSize * segmentsAcked;

      NS_LOG_INFO ("In SlowStart, updated to cwnd " << tcb->m_cWnd << " ssthresh " << tcb->m_ssThresh);
    }
  else
    {
      // Congestion avoidance: additive increase with RTT-based adjustments
      m_inCongestionAvoidance = true;

      uint32_t increasePerAck = CalculateIncrease (tcb);

      // Standard AIMD: increase by 1 MSS per RTT
      // This translates to: increase = (MSS * MSS) / cwnd per ACK
      uint32_t adder = std::max (1U, (increasePerAck * tcb->m_segmentSize) / tcb->m_cWnd);

      tcb->m_cWnd += adder * segmentsAcked;

      NS_LOG_INFO ("In CongAvoid, updated to cwnd " << tcb->m_cWnd <<
                   " ssthresh " << tcb->m_ssThresh <<
                   " adder " << adder);
    }
}

uint32_t
TcpMlCong::GetSsThresh (Ptr<const TcpSocketState> tcb, uint32_t bytesInFlight)
{
  NS_LOG_FUNCTION (this << tcb << bytesInFlight);

  // Multiplicative decrease: reduce cwnd by half
  uint32_t ssthresh = std::max (2 * tcb->m_segmentSize, bytesInFlight / 2);

  NS_LOG_DEBUG ("Updated ssthresh to " << ssthresh);

  // Reset consecutive increments counter on loss
  m_consecutiveIncrements = 0;

  return ssthresh;
}

} // namespace ns3
