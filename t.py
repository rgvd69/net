from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import Controller, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

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

    # Dictionary to store throughput results
    results = {}

    for scheme in schemes:
        # Set the congestion control scheme
        for h in [h1, h2, h3, h4]:
            h.cmd('sysctl -w net.ipv4.tcp_congestion_control=%s' % scheme)

        # Start TCP server on H4
        h4.cmd('iperf -s &')

        # Measure the throughput and network latency from H1, H2, and H3 to H4
        for h in [h1, h2, h3]:
            print('Iperf throughput from %s to H4 with %s:' % (h.name, scheme))
            iperf_output = h.cmd('iperf -c %s -t 10' % h4.IP())
            print(iperf_output)

            # Store throughput result
            results[(h.name, scheme)] = iperf_output.split()[7]  # assuming the throughput is the 8th word in the output

            print('Ping latency from %s to H4 with %s:' % (h.name, scheme))
            ping_output = h.cmd('ping -c 4 %s' % h4.IP())
            print(ping_output)

        # Close TCP server on H4
        h4.cmd('pkill iperf')

    # Stop tcpdump on s1-eth1
    s1.cmd('pkill tcpdump')

    # Print throughput results in a table format
    print('Throughput results:')
    print('Host\tScheme\tThroughput')
    for (host, scheme), throughput in results.items():
        print('%s\t%s\t%s' % (host, scheme, throughput))

    # ... rest of your code ...

    net.pingAll()


    CLI(net)
    s1.cmd('pkill -SIGINT tcpdump')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
