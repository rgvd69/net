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
    # Set the congestion control scheme to Vegas
    for h in [h1, h2, h3, h4]:
        h.cmd('sysctl -w net.ipv4.tcp_congestion_control=vegas')

    # Start iperf server on H4
    h4.cmd('iperf -s &')

    # Measure the throughput from H1 to H4
    print('Iperf throughput:')
    iperf_output = h1.cmd('iperf -c %s -t 10' % h4.IP())
    print(iperf_output)


    s1.cmd('tcpdump -i s1-eth1 -w r1.pcap &')  # replace 's1-eth1' with the name of the interface you want to capture on
    # Assign IP addresses
    for i in range(1, 5):
        net.get('h{}'.format(i)).setIP('192.168.{}.{}'.format((i-1)//2+1, 100+(i-1)%2), intf='h{}-eth0'.format(i))

    h4.cmd('python -m SimpleHTTPServer 80 &')

    h1.cmd('nc -1 1234 &')
    h2.cmd('nc -1 1234 &')
    h3.cmd('nc -1 1234 &')

    net.pingAll()


    CLI(net)
    s1.cmd('pkill -SIGINT tcpdump')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
