# ovirt-security-groups-demo
Ansible roles and tools to demo networking API security groups in oVirt

## Motivation and goals
Configure fine grained access control to / from the oVirt VMs attached to
external networks in OVN. Configuring access to those VMs is based on:
* Ports
* Protocols
* Remote IPs
* Group membership
* Ether type

In the networking API, defined in OpenStack by Neutron, there is an entity to
enable these use cases, through [security groups](https://developer.openstack.org/api-ref/network/v2/#security-groups-security-groups).
Using security groups, the user could - for instance - configure ICMP access to
all the VMs in OVN (or a subset of VMs), limit the traffic in the OVN external
networks to web traffic (e.g. tcp port 80). More complex scenarios can be
achieved, for instance, scenarios where some VMs can access a set of services,
whereas others cannot. This latter scenario can be configured either by IP,
subnet CIDR, or at an higher abstraction level, through group membership.

In oVirt, this networking API concept was implemented in the
[ovirt-provider-ovn](https://github.com/oVirt/ovirt-provider-ovn) project, and
a thorough design document for that feature is found at the following
[feature page ](https://ovirt.org/develop/release-management/features/network/networking-api-security-groups.html).

The goal of this repo is to provide tools to help the configuration of
security groups, since currently there is no official supported way to do so
other than through the provider's RESTful interface. Some example
configurations are also provided in this README.

## Provided tools
This repo adds tools to help manage the security groups in oVirt, since
currently there is no supported mechanism to provision security groups, other
than the REST API, and ManageIQ. ManageIQ also doesn't fully support security
groups, since it lacks a way to attach security groups to logical ports.

This repo provides the following tools:
* list_openstack_entities.py: python script that lists the logical ports or
  the security groups found in the system. It is very useful to get the IDs
  of the desired security group, and/or logical port.

  **NOTE:** the openstack CLI could also be used.
* update_port_security ansible playbook: this playbook's goal is to update
  port security for the target entities - whether they are networks, or ports.
* update_ports ansible playbook: this playbook's goal is to update the port's
  security group membership. Can clear the security groups of a logical port.
* create_icmp_security_group: this playbook creates (or deletes) a security
  group and provisions it with a rule allowing ICMP traffic.

  **NOTE:** this playbook provides an example on how the user can configure
  rules enabling access based on protocol - e.g. to all VMs.
* create_web_based_security_group.yml: this playbook creates (or deletes)
  security groups - and rules - to set up a web based scenario.

  **NOTE:** this playbook is meant as a configuration example of a scenario
  enabling access to a subset of VMs, by using group membership.

## Requirements
* python
* ansible
* openstacksdk

To properly install openstacksdk, execute:

```bash
pip install --user -r requirements.txt
```

That will install openstacksdk from pip with the correct dependencies, which
are listed in the [requirements.txt](requirements.txt) file.

### Connection to oVirt-engine
The connection to oVirt engine uses [openstacksdk](https://docs.openstack.org/openstacksdk/latest/). Please refer to its
documentation on [how to connect](https://docs.openstack.org/openstacksdk/latest/user/guides/connect.html).

The preferred connection mechanism is through the configuration file - i.e.
[clouds.yml](playbooks/clouds.yml). Update it to reflect your oVirt engine
configuration.

## Security group context

### Port Security
The networking API port security parameter has two different objectives: it
limits the MAC addresses that can communicate via the logical port, and
also indicates that security groups are applied to the logical port.
This means that a port with active port security, that doesn't belong to any
security group, will be isolated from the network.

In oVirt, port security is enabled by default. Despite that, connectivity
between the VMs is provided out of the box, through the
[Default group](#default-group) concept.

Port security is an attribute applied to the logical port, as well as to the
logical network. Port security at network level means that logical ports
created in that network will inherit the port security value from the
network - unless specified at port level.

Updates to the port security at network level **will not** cascade down to the
existing ports - i.e. it will only impact newly created ports.

In oVirt, the user can set the port security for the logical network through
the UI; its value can be either enabled, disabled, or unspecified - in which
case, it will default to the configuration value defined in the [port-security-enabled-default](https://github.com/oVirt/ovirt-provider-ovn#section-network)
attribute.

#### Updating port security on ports or networks

In this section it is shown how to use the sample ansible playbook to configure
the port security of networks and ports.

```bash
# update the port security of a single port
ansible-playbook -i localhost update_port_security.yml \
  --extra-vars="port_security_enabled=true port_uuid=<the_port_uuid>"

# update the port security of all ports attached to a logical network
# and of the network itself.
# Since updates to the network do not cascade down to the network ports, the
# playbook filters all ports belonging to the network and updates them.
ansible-playbook -i localhost update_port_security.yml \
  --extra-vars="port_security_enabled=true network_uuid=<the_network_uuid>"

# update the port security of all logical ports found in the system
ansible-playbook -i localhost update_port_security.yml \
  --extra-vars="port_security_enabled=true"

```

### Entity objects on the networking API
The two relevant entities on the networking API are **security groups** and
**security group rules**.

A security group operates as a container of rules, and can be applied to ports.
The intended use case, is for a user to create a group, add a set of rules to
it, and finally, attach the group to a (set of) port(s).

A security group rule specifies which type of traffic (using L3 / L4 semantics)
can access - or exit - the VM. They are scoped to the security group - i.e. the
rules can have the same data **whenever** they belong to different groups.
A security group rule can also be applied to either *ingress* - traffic incoming to the VM - or *egress* - traffic outgoing from the VM.

The *knobs* on a security group are:
* IP protocol
* ethertype - ipv4 / ipv6
* L4 port range - use max == min to open a single port
* remote ip prefix (using a CIDR), or a single IP
* remote group membership
* direction

Their APIs can be found in:
* [security groups](https://developer.openstack.org/api-ref/network/v2/#security-groups-security-groups)
* [security group rules](https://developer.openstack.org/api-ref/network/v2/#security-group-rules-security-group-rules)

### Default group
The **Default** group's goal is to allow access between all VMs out of the box.

To implement the Default group, four rules are used:
* allow all ingress Ipv4 belonging to the Default group
* allow all ingress Ipv6 belonging to the Default group
* allow all egress Ipv4
* allow all egress Ipv6

When a VM is created, having **port-security-enabled** active, will be
automatically added to the **Default** group, which will allow all VMs
to communicate by default - i.e. the **ingress** rules will be matched,
and traffic allowed into the VM.

The outgoing traffic, which will match the egress rules, allows the VM to
communicate to the outside world.

#### Limitations of the Default group
The Default group cannot be deleted. Nevertheless, its rules can, and new
rules can also be added to it.

Remember that deleting the rules within the Default group leads to a loss of
connectivity between the VMs whose logical ports are members of the Default
group.

## Demo scripts
### Flat scenario

Using the tools provided in this repo, the Default group concept will be
showcased, and two different configurations will be shown: the first will
grant ICMP access amongst a set of VMs, the second will grant access to a web
server running on one VM. No other kinds of L3 traffic will be allowed.

#### ICMP configuration
The following ASCII diagram portrays the goal for this scenario.
In it, there are 3 VMs, all of them belonging to the *icmp* security group.
That group features a single security group rule, allowing ingress ICMP
protocol traffic to the VMs.

```
       +---------------+
       |      nisu     |
       |  <dynamic_ip> |
       |     icmp      |
       +---------------+
           |       x
         icmp     web
           |       x
       +---------------+       +---------------+
       |     net1      |-icmp--|    web_client |
       | 172.20.50.0/24|x-web-x|  <dynamic_ip> |
       +---------------+       |      icmp     |
               |               +---------------+
       +---------------+
       |   web_server  |
       |  <dynamic_ip> |
       |     icmp      |
       +---------------+

```

To configure the above scenario, create one external logical network - having
a subnet on top - through oVirt's UI.

Then, create 3 VMs attached to that external logical network. This can also
be achieved through the UI.

To create the icmp security group, you can use the [create_icmp_security_group](playbooks/create_icmp_security_group.yml) playbook. Make sure your *clouds.yml*
file is properly configured, since it specifies the authentication URL and
credentials from the ansible client to your oVirt engine.

```bash
ansible-playbook -i localhost create_icmp_security_group.yml
```

Now that the security group - and rule - are created, the logical ports group
membership has to feature the ICMP group. To do that, it is required to know
the security group ID of the icmp group.
Afterwards, use the *update_ports* playbook, as shown in the example below:

```bash
ansible-playbook -i localhost update_ports.yml --extra-vars="sec_groups=<icmp_security_group_id>"
```

**NOTE:** to find the *icmp_security_group_id*, use the [list_openstack_entities.py](list_openstack_entities.py) script - or the OpenStack CLI.

The playbook mentioned above can update a single port, or all the existing
ports. When the *port_uuid* variable is not specified, the later occurs - i.e.
all ports will be members of the *icmp* group.

Now the user can see that pinging the VMs is possible, but all other types of
traffic are blocked.

#### Web server configuration
In this example, the previous scenario will be reversed - i.e. ICMP traffic
will be blocked, whereas web traffic will be allowed. The scenario is expressed
through the following ASCII diagram:

```bash
       +---------------+
       |      nisu     |
       |  <dynamic_ip> |
       |      web      |
       +---------------+
           x       |
         icmp     web
           x       |
       +---------------+        +---------------+
       |     net1      |xxicmpxx|    web_client |
       | 172.20.50.0/24|---web--|  <dynamic_ip> |
       +---------------+        |      web      |
               |                +---------------+
       +---------------+
       |   web_server  |
       |  <dynamic_ip> |
       |      web      |
       +---------------+
```

The [create_web_based_security_group](playbooks/create_web_based_security_group.yml) playbook can be used to create a new
security group, and to provision it with a rule that allows incoming tcp
traffic to port 80. As previously, the logical ports security group membership has to be updated.

```bash
# create the web security group
ansible-playbook -i localhost create_web_based_security_group.yml

# update all the logical ports in the system, making them members of the
# web group
ansible-playbook -i localhost update_ports.yml --extra-vars="sec_groups=<web_security_group_id>"
```

**NOTE:** to find the *icmp_security_group_id*, use the [list_openstack_entities.py](list_openstack_entities.py) script - or the OpenStack CLI.

Now the user can see that pinging is no longer allowed, but web traffic is.

Both types of traffic can be enabled, by setting the ports to be members of
both groups:

```bash
ansible-playbook -i localhost update_ports.yml --extra-vars="sec_groups=<web_security_group_id>,<icmp_security_group_id>"
```

### Group membership based access scenario
The following ASCII diagram portrays an example on how security groups can be
used to achieve an advanced configuration where some VMs can access a service
whereas others cannot. It uses the *remote_group_id* security group rule
parameter to provide access to the web service, based on group membership.

```
       +---------------+
       |      nisu     |
       |  <dynamic_ip> |
       |    Default    |
       +---------------+
               x
               x
               x
       +---------------+       +---------------+
       |     net1      |       |   web_client  |
       | 172.20.50.0/24|-------|  <dynamic_ip> |
       +---------------+       |   web_clients |
               |               +---------------+
       +---------------+
       |   web_server  |
       |  <dynamic_ip> |
       |  web_servers  |
       +---------------+

```

In the scenario portrayed above, the *web_server* vm belongs to the
*web_servers* security group. That group features a single rule, that opens
tcp port 80 traffic to clients **belonging** to the ***web_clients*** security
group.

The *web_client* vm belongs in turn to the *web_clients* group, which makes it
able to access the web service located in the *web_server* VM.

The nisu VM belongs to the *Default* security group; as a result, it is not
able to access to web service located in the *web_server* VM.

To achieve such a scenario, the following playbooks should be executed:

```bash
# create the web server and web client groups
ansible-playbook -i localhost create_web_based_security_group.yml \
  --extra-vars="provision_web_client_group=true"

# attach the Default group to the nisu VM
ansible-playbook -i localhost update_ports.yml \
  --extra-vars="port_uuid=<nisu_vm_uuid> sec_groups=Default"

# attach the web_servers group to the web_server VM
ansible-playbook -i localhost update_ports.yml \
  --extra-vars="port_uuid=<web_server_vm_id> sec_groups=<web_servers_group_id>"

# attach the web_clients group to the web_client VM
ansible-playbook -i localhost update_ports.yml \
  --extra-vars="port_uuid=<web_client_vm_id> sec_groups=<web_clients_group_id>"

```

**NOTE:** to find the security group IDs and the port IDs, use the [list_openstack_entities.py](list_openstack_entities.py) script - or the OpenStack CLI.
