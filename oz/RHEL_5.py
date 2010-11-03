import Guest
import shutil
import subprocess
import re
import ozutil

class RHEL5Guest(Guest.CDGuest):
    def __init__(self, update, arch, url, ks, nicmodel, diskbus):
        Guest.CDGuest.__init__(self, "RHEL-5", update, arch, None, nicmodel, None, None, diskbus)
        self.ks_file = ks
        self.url = url

    def modify_iso(self):
        self.log.debug("Putting the kickstart in place")

        shutil.copy(self.ks_file, self.iso_contents + "/ks.cfg")

        self.log.debug("Modifying the boot options")
        f = open(self.iso_contents + "/isolinux/isolinux.cfg", "r")
        lines = f.readlines()
        f.close()
        for line in lines:
            if re.match("timeout", line):
                lines[lines.index(line)] = "timeout 1\n"
            elif re.match("default", line):
                lines[lines.index(line)] = "default customiso\n"
        lines.append("label customiso\n")
        lines.append("  kernel vmlinuz\n")
        lines.append("  append initrd=initrd.img ks=cdrom:/ks.cfg method=" + self.url + "\n")

        f = open(self.iso_contents + "/isolinux/isolinux.cfg", "w")
        f.writelines(lines)
        f.close()

    def generate_new_iso(self):
        self.log.debug("Generating new ISO")
        Guest.subprocess_check_output(["mkisofs", "-r", "-T", "-J", "-V",
                                       "Custom", "-b", "isolinux/isolinux.bin",
                                       "-c", "isolinux/boot.cat",
                                       "-no-emul-boot", "-boot-load-size", "4",
                                       "-boot-info-table", "-v", "-v",
                                       "-o", self.output_iso, self.iso_contents])

    def generate_install_media(self):
        self.get_original_iso(self.url + "/images/boot.iso")
        self.copy_iso()
        self.modify_iso()
        self.generate_new_iso()
        self.cleanup_iso()

def get_class(idl):
    update = idl.update()
    arch = idl.arch()
    key = idl.key()

    if idl.installtype() != 'url':
        raise Exception, "RHEL-5 installs must be done via url"

    url = ozutil.check_url(idl.url())

    if update == "GOLD" or update == "U1" or update == "U2" or update == "U3":
        ks = ozutil.generate_full_auto_path("rhel-5-jeos.ks")
        return RHEL5Guest(update, arch, url, ks, "rtl8139", None)
    if update == "U4" or update == "U5":
        ks = ozutil.generate_full_auto_path("rhel-5-virtio-jeos.ks")
        return RHEL5Guest(update, arch, url, ks, "virtio", "virtio")
    raise Exception, "Unsupported RHEL-5 update " + update
