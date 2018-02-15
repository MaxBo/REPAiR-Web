# Installing Vagrant

To download Vagrant for supported platforms, see [here](https://www.vagrantup.com/downloads.html)

# Installing VirtualBox

If choosing VirtualBox as your virtualization provider, see [here](https://www.virtualbox.org/wiki/Downloads).

You may have to enable hardware virtualization extensions in your BIOS before using it.

If running on Ubuntu, you may have to install a newer version of VirtualBox than what is available in the public repositories in order for it to work correctly with Vagrant.

## Install VirtualBox Guest Additions on the guest system

It is required in order to properly handle shared folders and communication between the host and the guest. Install it with the [Vagrant plugin](https://github.com/dotless-de/vagrant-vbguest):

```
vagrant plugin install vagrant-vbguest
```

The Vagrantfile relies on this plugin.

# Setting up REPAiR-Web with Vagrant & VirtualBox
Once Vagrant has been installed, you can start an environment by checking out the REPAiR-Web code, then changing to the directory which contains the Vagrantfile by typing:

    # Windows users will need to uncomment the line ending configuration option.
    git clone git@github.com:MaxBo/REPAiR-Web.git REPAiR-Web #--config core.autocrlf=input
    cd REPAiR-Web
    vagrant up

# Other Virtualization Providers

If you would like to use Parallels instead of VirtualBox, please run the following command:
```
vagrant up --provider=parallels
```
Please note that this requires the Parallels Vagrant plugin, which can be installed:
```
vagrant plugin install vagrant-parallels
```

Similarly, if you would like to use VMware Workstation instead of VirtualBox, please run the following command:
```
vagrant up --provider vmware_workstation
```
Please note that this requires the VMware Vagrant plugin, which can be installed:
```
vagrant plugin install vagrant-vmware-workstation
```

# Vagrant Provisioning

The initialization of the vagrant vm (`vagrant up`) will take about ten minutes at first.

You should be able to log into the running VM by typing:

    vagrant ssh

Within this login shell, you can build the code, run the server or the tests. With the initialization of the vm (provisioning), also the Node.js and Django server are started with hot reloading. Django is listening to `0.0.0.0:80` on the guest, which is forwarded to `localhost:8081` on the host.

The REPAiR-Web root folder (on host) is mapped to the `/home/vagrant/REPAiR-Web` folder on the guest.

See the details on how the vm is provisioned in `VagrantProvisionUbuntu1604.sh`

**Acknowledgement**

The majority of this description was taken from the [Hootenanny project](https://github.com/ngageoint/hootenanny/blob/master/VAGRANT.md)
