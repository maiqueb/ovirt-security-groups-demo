# ovirt-security-groups-demo
Ansible roles and tools to demo networking API security groups in oVirt

## Motivation and goals
Configure access to / from VMs attached to OVN logical networks, based on:
* Ports 
* Protocols
* Remote IPs
...

OpenStack currently defines means to do so, through [security groups](https://developer.openstack.org/api-ref/network/v2/#security-groups-security-groups).

Thus, the natural way to fulfill our goals, is G

Mimic networking API security groups / security group rules entities

## Port Security
TODO

## Entity objects on the networking API
The two relevant entities on the networking API are **security groups** and
**security group rules**.

A security group operates as a container of rules, and can be applied to ports.
The intended use case, is for a user to create a group, add a set of rules to
it, and finally, attach the group to a (set of) port(s).

A security group rule specifies which type of traffic (using L3 / L4 semantics)
can access - or exit - the VM. They are scoped to the security group - e.g. the
rules can have the same data **whenever** they belong to different groups.
A security group rule can also be applied to either *ingress* - traffic incomming to the VM - or *egress* - traffic outgoing from the VM.

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

## Default group
The **Default** group's goal is to allow access between all VMs out of the box.

To implement the Default group, four rules are used:
* allow all ingress Ipv4 belonging to the Default group
* allow all ingress Ipv6 belonging to the Default group
* allow all egress Ipv4
* allow all egress Ipv6

When a VM is created, having **port-security-enabled** active, will be
automatically added to the **Default** group, which will allow all VMs
to communicate by default - e.g. the **ingress** rules will be matched,
and traffic allowed into the VM.

The outgoing traffic - e.g. will also match the egress rules - thus allowing
the VM to communicate to the outside world.

### Limitations of the Default group
The Default group cannot be deleted. Never-the-less, its rules can, and new
rules can also be added to it.

Remember that if you delete the rules within the Default group, the
connectivity between the VMs whose ports have it attached **will** break.

## Flat scenario
TODO

## Semantic based access scenario
TODO

