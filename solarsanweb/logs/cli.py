
import os
import configshell
import sh


class Logs(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Logs, self).__init__('logs', parent)

    def ui_command_tail(self):
        '''
        tail - Tails syslog
        '''
        #ccze = sh.ccze.bake('-A')
        #tail = sh.tail.bake('-qF', '/var/log/debug', '/var/log/syslog')
        #if grep:
        #    ret = grep(ccze(tail(_piped=True), _piped=True), '--', grep, _iter=True, _err_to_out=True)
        #else:
        #    #ret = ccze(tail(_iter=True), _iter=True, _err_to_out=True)
        #for line in ret:
        #    print line.rstrip("\n")
        os.system("tail -qF /var/log/debug /var/log/syslog | ccze -A")
