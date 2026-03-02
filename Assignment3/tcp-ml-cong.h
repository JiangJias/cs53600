/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2026
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */

#ifndef TCP_ML_CONG_H
#define TCP_ML_CONG_H

#include "ns3/tcp-congestion-ops.h"
#include "ns3/tcp-recovery-ops.h"

namespace ns3 {

/**
 * \ingroup congestionOps
 *
 * \brief An implementation of ML-based TCP congestion control
 *
 * This congestion control algorithm is based on machine learning insights
 * from Assignment 2. It implements AIMD-based congestion control with
 * RTT-aware adjustments and throughput optimization.
 *
 * Key principles:
 * 1. Additive Increase during congestion avoidance (when no loss)
 * 2. Multiplicative Decrease on loss detection
 * 3. RTT-based adjustments to avoid queue buildup
 * 4. Throughput-aware optimization
 * 5. Conservative behavior under network instability
 */
class TcpMlCong : public TcpNewReno
{
public:
  /**
   * \brief Get the type ID.
   * \return the object TypeId
   */
  static TypeId GetTypeId (void);

  /**
   * Create an unbound tcp socket.
   */
  TcpMlCong (void);

  /**
   * \brief Copy constructor
   * \param sock the object to copy
   */
  TcpMlCong (const TcpMlCong& sock);

  virtual ~TcpMlCong (void);

  virtual std::string GetName () const;

  virtual void IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked);
  virtual uint32_t GetSsThresh (Ptr<const TcpSocketState> tcb, uint32_t bytesInFlight);
  virtual Ptr<TcpCongestionOps> Fork ();

  /**
   * \brief Update RTT measurements
   * \param tcb internal congestion state
   * \param segmentsAcked count of segments acked
   */
  virtual void PktsAcked (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked, const Time& rtt);

protected:
  /**
   * \brief Calculate the appropriate cwnd increase based on network conditions
   * \param tcb the socket state
   * \return the increase amount
   */
  uint32_t CalculateIncrease (Ptr<TcpSocketState> tcb);

  /**
   * \brief Check if we should be more conservative due to RTT increases
   * \param currentRtt the current RTT
   * \return true if we should slow down
   */
  bool ShouldSlowDown (Time currentRtt);

private:
  Time m_minRtt;              //!< Minimum RTT observed
  Time m_baseRtt;             //!< Baseline RTT for comparison
  double m_alpha;             //!< RTT penalty weight
  double m_beta;              //!< Loss penalty weight
  uint32_t m_consecutiveIncrements; //!< Count of consecutive cwnd increments
  uint32_t m_lastCwnd;        //!< Last cwnd value
  Time m_lastRtt;             //!< Last RTT measurement
  double m_rttThreshold;      //!< RTT increase threshold (as fraction of baseline)
  bool m_inCongestionAvoidance; //!< Flag for congestion avoidance phase
};

} // namespace ns3

#endif /* TCP_ML_CONG_H */
