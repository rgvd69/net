from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import Controller, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

import threading

class CustomTopo(Topo):
    "Custom topology with 3 routers (switch+host) and 6 hosts."

    def build(self):
        # Add hosts and switches
        hosts = [self.addHost('h{}'.format(i)) for i in range(1, 5)]
        switches = [self.addSwitch('s{}'.format(i)) for i in range(1, 3)]

        # Add links between hosts and switches
        for i in range(2):
            self.addLink(hosts[i*2], switches[i])
            self.addLink(hosts[i*2+1], switches[i])


        # Add links between switches
        self.addLink(switches[0], switches[1])



def run():
    "Create and run the network"
    topo = CustomTopo()
    net = Mininet(topo=topo, controller=Controller, switch=OVSSwitch)
    h1, h2, h3, h4, s1, s2 = net.get('h1', 'h2','h3', 'h4', 's1', 's2')

    net.start()

    # Start tcpdump on s1-eth1
    s1.cmd('tcpdump -i s1-eth1 -w output.pcap &')

    # List of congestion control schemes to test
    schemes = ['reno', 'cubic', 'bbr', 'vegas']
    h4.cmd('iperf -s &')

    for scheme in schemes:
        print('Testing scheme %s' % scheme)
        # Run the hosts sequentially
        print('Running hosts sequentially')
        for h in [h1, h2, h3]:
            measure_throughput_and_latency(h, h4, scheme)

        # Run the hosts simultaneously
        print('Running hosts simultaneously')
        threads = []
        for h in [h1, h2, h3]:
            t = threading.Thread(target=measure_throughput_and_latency, args=(h, h4, scheme))
            t.start()
            threads.append(t)

        # Wait for all threads to finish
        for t in threads:
            t.join()


    net.pingAll()


    CLI(net)
    s1.cmd('pkill -SIGINT tcpdump')
    net.stop()

def measure_throughput_and_latency(h, h4, scheme):
    print('Iperf throughput from %s to H4 with %s:' % (h.name, scheme))
    iperf_output = h.cmd('iperf -c %s -t 10' % h4.IP())
    print(iperf_output)


    print('Ping latency from %s to H4 with %s:' % (h.name, scheme))
    ping_output = h.cmd('ping -c 4 %s' % h4.IP())
    print(ping_output)


if __name__ == '__main__':
    setLogLevel('info')
    run()
