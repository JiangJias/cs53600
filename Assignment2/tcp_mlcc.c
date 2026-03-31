#include <linux/module.h>
#include <net/tcp.h>

/* * MLCC: Machine Learning derived Congestion Control
 * A hybrid congestion control algorithm based on observations from Assignment 2.
 * It combines loss-based signals with delay-based queue management.
 */

static void tcp_mlcc_cong_avoid(struct sock *sk, u32 ack, u32 acked)
{
    struct tcp_sock *tp = tcp_sk(sk);
    u32 min_rtt = tcp_min_rtt(tp);
    u32 curr_rtt = tp->srtt_us >> 3; 
    
    // Do nothing if we are not cwnd limited
    if (!tcp_is_cwnd_limited(sk))
        return;

    // Classic Slow Start phase
    if (tcp_in_slow_start(tp)) {
        tcp_slow_start(tp, acked);
        return;
    }

    /* * Congestion Avoidance Phase
     * Incorporating Assignment 2 logic: 
     * If current RTT is > 20% higher than min_rtt, it indicates queue buildup (bufferbloat).
     */
    if (curr_rtt > min_rtt + (min_rtt / 5)) {
        // Delay is high: stop growing to allow the bottleneck queue to drain.
        // This corresponds to the conservative "+= 0.5/cwnd" or flatlining rule.
        return; 
    } else {
        // Delay is optimal: execute standard AIMD additive increase (+ 1 MSS per RTT).
        tcp_cong_avoid_ai(tp, tp->snd_cwnd, 1);
    }
}

/* * Multiplicative decrease logic upon packet loss 
 */
static u32 tcp_mlcc_ssthresh(struct sock *sk)
{
    const struct tcp_sock *tp = tcp_sk(sk);
    
    // On packet loss, follow Assignment 2 logic: cwnd = max(cwnd / 2, 2)
    return max(tp->snd_cwnd >> 1U, 2U);
}

/* * Register the TCP congestion control structure 
 */
static struct tcp_congestion_ops tcp_mlcc __read_mostly = {
    .flags          = TCP_CONG_NON_RESTRICTED,
    .name           = "mlcc",
    .owner          = THIS_MODULE,
    .ssthresh       = tcp_mlcc_ssthresh,
    .cong_avoid     = tcp_mlcc_cong_avoid,
    .undo_cwnd      = tcp_reno_undo_cwnd,
};

static int __init tcp_mlcc_register(void)
{
    BUILD_BUG_ON(sizeof(struct tcp_congestion_ops) != sizeof(struct tcp_congestion_ops));
    return tcp_register_congestion_control(&tcp_mlcc);
}

static void __exit tcp_mlcc_unregister(void)
{
    tcp_unregister_congestion_control(&tcp_mlcc);
}

module_init(tcp_mlcc_register);
module_exit(tcp_mlcc_unregister);

MODULE_AUTHOR("Student");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("ML-derived TCP Congestion Control");