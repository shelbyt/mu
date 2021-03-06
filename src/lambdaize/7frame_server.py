#!/usr/bin/python

import os

from libmu import server, TerminalState, CommandListState

class ServerInfo(object):
    host_addr = None
    port_number = 13579

    video_name = "sintel-1k"
    num_offset = 1
    num_parts = 1
    overprovision = 25

    lambda_function = "mk7frames"
    regions = ["us-east-1"]
    bucket = "excamera-us-east-1"
    out_file = None
    profiling = None

    cacert = None
    srvcrt = None
    srvkey = None

class FinalState(TerminalState):
    extra = "(finished)"

class Make7FrameState(CommandListState):
    extra = "(configuring lambda worker)"
    nextState = FinalState
    pipelined = False
    commandlist = [ ("OK:HELLO", "retrieve:{0}/{1}.y4m\0##TMPDIR##/prev.y4m")
                  , "run:/usr/bin/perl ./y4m_chop.pl \"##TMPDIR##/prev.y4m\" \"##TMPDIR##/frames_\" 1"
                  , "run:rm \"##TMPDIR##/frames_000000.y4m\" \"##TMPDIR##/frames_000001.y4m\" \"##TMPDIR##/frames_000002.y4m\" \"##TMPDIR##/frames_000003.y4m\" \"##TMPDIR##/frames_000004.y4m\" \"##TMPDIR##/prev.y4m\""
                  , "retrieve:{0}/{2}.y4m\0##TMPDIR##/this.y4m"
                  , "run:tail -n +2 \"##TMPDIR##/this.y4m\" >> \"##TMPDIR##/frames_000005.y4m\""
                  , "upload:{3}/{2}.y4m\0##TMPDIR##/frames_000005.y4m"
                  , "quit:"
                  ]

    def __init__(self, prevState, actorNum):
        super(Make7FrameState, self).__init__(prevState, actorNum)
        inName = "%s-y4m_06" % ServerInfo.video_name
        outName = "%s-y4m_07" % ServerInfo.video_name
        thisNum = self.actorNum + ServerInfo.num_offset
        thisNStr = "%08d" % thisNum
        prevNStr = "%08d" % (thisNum - 1)
        self.commands = [ s.format(inName, prevNStr, thisNStr, outName) if s is not None else None for s in self.commands ]

def run():
    server.server_main_loop([], Make7FrameState, ServerInfo)

def main():
    server.options(ServerInfo)

    # launch the lambdas
    event = { "mode": 1
            , "port": ServerInfo.port_number
            , "addr": ServerInfo.host_addr
            , "nonblock": 0
            , "cacert": ServerInfo.cacert
            , "srvcrt": ServerInfo.srvcrt
            , "srvkey": ServerInfo.srvkey
            , "bucket": ServerInfo.bucket
            }
    server.server_launch(ServerInfo, event, os.environ['AWS_ACCESS_KEY_ID'], os.environ['AWS_SECRET_ACCESS_KEY'])

    # run the server
    run()

if __name__ == "__main__":
    main()
