from math import log

distanceChart =((0,2000,2000,4000,6000,4000,4000,6000,6000),
(0,2000,2000,4000,2000,4000,4000,6000),
(0,4000,4000,2000,2000,4000,4000),
(0,2000,2000,4000,4000,6000),
(0,2000,4000,2000,4000),
(0,2000,2000,4000),
(0,2000,2000),
(0,2000),
(0,))

CALL = 0
CALL_TERMINATION = 1
CLUSTER_SIZE = 3
CHANNELS_PER_CLUSTER = 8

class Event(object):
    def __init__(self,eventType,time):
        self.eventType = eventType
        self.time=time   

class Call(Event):
    def __init__(self,number,time,cell,duration):
        super(Call,self).__init__(CALL,time)
        self.number=number
        self.cell=cell
        self.duration=duration
    def __str__(self):
        return str(self.number)+","+str(self.time)+","+str(self.cell)+","+str(self.duration)

class CallTermination(Event):
    def __init__(self,call,channel,cluster,sir,interferers):
        super(CallTermination,self).__init__(CALL_TERMINATION,call.time + call.duration)
        self.call=call
        self.channel=channel
        self.cluster=cluster
        self.sir=sir
        self.interferers=interferers
    def __str__(self):
        return str(self.call)+","+str(self.time)+","+str(self.channel)
        
        
class Cluster:
    def __init__(self,numberOfCells, numberOfChannels):
        self.numberOfCells=numberOfCells
        self.numberOfChannels=numberOfChannels
        self.channelOccupied=[None for i in range(numberOfChannels)]
        
    def allocateCall(self,clusters,call):
        sirs = []
        
        for i in range(self.numberOfChannels):
            if self.channelOccupied[i] is None:
                sir,interferers = self.calculateInterference(i,clusters,call)
                if sir > 22:
                    self.channelOccupied[i] = call
                    return (CallTermination(call,i,self,sir,interferers),None)
                else:
                    sirs.append(sir)
            else:
                sirs.append(None)
        return (None,sirs)
    
    def terminateCall(self,callTermination):
        self.channelOccupied[callTermination.channel]= None

    def calculateInterference(self,channel,clusters, call):
        s = 0
        interferers=[]
        
        for cluster in clusters:
            if cluster is self:
                continue
            occupyingCall = cluster.channelOccupied[channel]
            if occupyingCall is not None:
                d = calculateDistance(occupyingCall.cell, call.cell)
                if d != 0:
                    s += d**(-4)
                    interferers.append((occupyingCall.cell, d))
        if s == 0:
            sir = 35
        else:
            si = 1000**(-4)/s
            sir = 10*log(si,10)
        return (sir,interferers)

class Queue:
    def __init__(self):
        self.queue=[]
    def addEvent(self,event):
        foundIndex=None
        for i in range(len(self.queue)):
            e=self.queue[i]
            if e.time > event.time:
               foundIndex = i
               break
        if foundIndex is None:
            self.queue.append(event)
        else:
            self.queue.insert(foundIndex,event)

    def isEmpty(self):
        return len(self.queue)>0

    def popEvent(self):
        event, self.queue = self.queue[0], self.queue[1:]
        return event

def calculateDistance(cell1,cell2):
    cell1-=1
    cell2-=1
    if cell1>cell2:
        cell1,cell2=cell2,cell1
    #print cell1,cell2
    d = distanceChart[cell1][cell2-cell1]    
    return d
            
def readFile(fname):
    with open(fname) as f:
        content = f.readlines()
    return content[1:]

def buildQueue(content):
    queue = Queue() 
    for line in content:
        numbers = [int(x) for x in line.split()]
        e = Call(numbers[0],numbers[1],numbers[2],numbers[3])
        queue.addEvent(e)
    return queue

def simulateFromFile(fname):    
    content = readFile(fname)
    queue = buildQueue(content)
    clusters = [Cluster(CLUSTER_SIZE,CHANNELS_PER_CLUSTER) for i in range(3)]
    acceptedCalls = 0
    rejectedCalls = 0
    totalSirs = 0
    while queue.isEmpty():
        event = queue.popEvent()
        if event.eventType == CALL:            
            clusterIndex = (event.cell -1)/CLUSTER_SIZE
            cluster=clusters[clusterIndex]
            result,sirs = cluster.allocateCall(clusters,event)
            if result is None:
                rejectedCalls += 1
                s = "New Call: Number=%d StartTime=%d Cell=%d Duration=%d Rejected\nReasons: " %(event.number,event.time,event.cell,event.duration) 
                for i in range(len(sirs)):
                    sir=sirs[i]
                    if sir is None:
                        s += "%d/In Use " %(i+1,)
                    else:
                        s += "%d/Low SIR=%.0f dB " %(i+1,sir)
                print s
            else:
                acceptedCalls += 1
                totalSirs += result.sir
                print "New Call: Number=%d StartTime=%d Cell=%d Duration=%d Accepted Channel=%d SIR=%.0f dB Interferers:%s" %(event.number,event.time,event.cell,event.duration,result.channel,result.sir,result.interferers)                
                queue.addEvent(result)
        else:
            print "Disconnect: Number=%d StartTime=%d EndTime=%d Cell=%d Duration=%d Channel=%d" %(event.call.number,event.call.time,event.time,event.call.cell,event.call.duration,event.channel)
            event.cluster.terminateCall(event)
    gos= 100.*rejectedCalls/(acceptedCalls+rejectedCalls)
    averageSir = totalSirs/acceptedCalls
    print "Totals: %d calls accepted, %d calls rejected, %.2f%% GOS, Average SIR =%.1f dB" %(acceptedCalls,rejectedCalls,gos,averageSir)

simulateFromFile("input-high.txt")

