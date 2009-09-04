from dCacheInfo import *

class dCacheInfoPool(dCacheInfo):

    def __init__(self,category,timestamp,storage_dir):

        # inherits from the ModuleBase Class
        dCacheInfo.__init__(self,category,timestamp,storage_dir)

	config = self.readConfigFile('./happycore/dCacheInfoPool')
        self.readDownloadRequests(config)
	self.addCssFile(config,'./happycore/dCacheInfoPool')


        self.poolType = self.mod_config.get('setup','pooltype')

        ## space can be shown in GB or in TB
        try:
            self.unit = self.mod_config.get('setup','unit')
        except:
            self.unit = 'GB'

        if self.unit == 'GB':
            self.fromByteToUnit = 1024*1024*1024
        elif self.unit == 'TB':
            self.fromByteToUnit = 1024*1024*1024*1024
        else:
            print 'Warning: unknown unit in '+self.__module__+'. Must be "GB" or "TB". Using "GB" ...'
            self.fromByteToUnit = 1024*1024*1024



        self.poolAttribNames = {}
        self.poolAttribNames['total'] = {'name':'Total Space' , 'unit':self.unit }
        self.poolAttribNames['free'] = {'name':'Free Space'                , 'unit':self.unit}
        self.poolAttribNames['used'] = {'name':'Used Space'                 , 'unit':self.unit}
        self.poolAttribNames['precious'] = {'name':'Precious Space'             , 'unit':self.unit}
        self.poolAttribNames['removable'] = {'name':'Removable Space'            , 'unit':self.unit}
        self.poolAttribNames['poolnumber'] = {'name':'Pools'                      , 'unit':''}
        self.poolAttribNames['poolcritical'] = {'name':'Pools with status warning ' , 'unit':''}
        self.poolAttribNames['poolwarning'] = {'name':'Pools with status critical' , 'unit':''}


        
        self.thresholds = {}
        self.thresholds['limit_global_critical'] = {}
        self.thresholds['limit_local_critical'] = {}
        self.thresholds['limit_global_warning'] = {}
        self.thresholds['limit_local_warning'] = {}

        self.getThresholds(config)
        self.getThresholds(self.mod_config)


        for entry in self.getRatioVar(''):
            att = entry.split("/")
            name = self.poolAttribNames[att[0]]['name']+" / "+ self.poolAttribNames[att[1]]['name']
            self.poolAttribNames[entry] =  {'name':name , 'unit':'%%'}


        for entry in self.poolAttribNames:
            if self.poolAttribNames[entry]['unit'] != '':
                self.poolAttribNames[entry]['webname'] = self.poolAttribNames[entry]['name']+" ["+self.poolAttribNames[entry]['unit']+"]"
            else:
                self.poolAttribNames[entry]['webname'] = self.poolAttribNames[entry]['name']
            


        # List of Local Pool Attributes
        self.localAttribs = []
        self.localAttribs.append('total') 
        self.localAttribs.append('free') 
        self.localAttribs.append('used') 
        self.localAttribs.append('precious') 
        self.localAttribs.append('removable') 
 

        # List of Pool Summary Attributes
        self.globalSummary = []
        self.globalSummary.append('poolnumber')
        self.globalSummary.append('poolcritical')
        self.globalSummary.append('poolwarning')
        for val in self.localAttribs:
            self.globalSummary.append(val)



        self.globalRatios =  self.getRatioVar('global')
        self.localRatios =  self.getRatioVar('local')
        


        
	self.db_keys["details_database"] = StringCol()
        self.db_values["details_database"] = ""

        self.sumInfo = {}
        for att in self.globalSummary:
            self.db_keys[ att ] = FloatCol()
            self.db_values[ att ] = None
            self.sumInfo[  att ] = 0





    def getRatioVar(self,ident):
        poolAttribsRatios = {}
        for cutType in self.thresholds.keys():
            if cutType.count(ident) > 0:
                for cut in self.thresholds[cutType]:
                    if cut.count('/') > 0:
                        if not cut in poolAttribsRatios:
                            poolAttribsRatios[cut] = {}
        return poolAttribsRatios.keys()



    def getThresholds(self,config):
        for sec in self.thresholds.keys():
            if  config.has_section(sec):
                for i in config.items(sec):
                    self.thresholds[sec][i[0]] = i[1]



    def limitExceeded(self,thePoolInfo,cat):
        exceeded = False
        theThresholds = self.thresholds[cat]
        for check in theThresholds.keys():
            checkList = check.split("/")

            for val in checkList:
                if not val in thePoolInfo:
                    print "Warning: No such variable for limit check in "+self.__module__+": "+val
                    print "         Return that limit is exceeded."
                    return True


            theRelVal = 0.
            if len(checkList) == 1:
                theRelVal = float(thePoolInfo[checkList[0]])
            elif len(checkList) == 2:
                theRelVal = float(thePoolInfo[checkList[0]])/float(thePoolInfo[checkList[1]])


            theCond = str(theThresholds[check])[:1]
            theRef = float(str(theThresholds[check])[1:])


            if theCond == ">":
                if theRelVal > theRef:
                    exceeded = True
            elif theCond == "<":
                if theRelVal < theRef:
                    exceeded = True
            else:
                print "Warning: No such condition "+check+" "+theThresholds[check]

#            print checkList
#            print str(theRelVal)+theCond+str(theRef)+" --> "+str(exceeded)


        return exceeded



    def run(self):

        thePoolInfo = self.getPoolInfo(self.poolType)
        
        
        # make poolAttrib as GB or TB
        for pool in thePoolInfo.keys():
            for att in self.localAttribs:
                if att in thePoolInfo[pool]:
                    thePoolInfo[pool][att] = float(thePoolInfo[pool][att]) / self.fromByteToUnit




        details_database = self.__module__ + "_table_details"
        self.db_values["details_database"] = details_database

        
	details_db_keys = {}
	details_db_values = {}
        
        details_db_keys["poolname"] = StringCol()
        details_db_keys["poolstatus"] = FloatCol()
	
	# write global after which the query will work
	details_db_keys["timestamp"] = IntCol()
	details_db_values["timestamp"] = self.timestamp

	# create index for timestamp
	details_db_keys["index"] = DatabaseIndex('timestamp')


        for att in self.localAttribs:
            details_db_keys[ att ] = FloatCol()

        # lock object enables exclusive access to the database
	self.lock.acquire()

	Details_DB_Class = type(details_database, (SQLObject,), details_db_keys )

	Details_DB_Class.sqlmeta.cacheValues = False
	Details_DB_Class.sqlmeta.fromDatabase = True
		
	# if table is not existing, create it
        Details_DB_Class.createTable(ifNotExists=True)

        
        for pool in thePoolInfo.keys():
            self.sumInfo['poolnumber'] +=1
            details_db_values["poolname"] = pool

            if self.limitExceeded(thePoolInfo[pool],'limit_local_critical') == True:
                # Set 0.0 for Pool is Critical
                details_db_values["poolstatus"] = 0.
            elif self.limitExceeded(thePoolInfo[pool],'limit_local_warning') == True:
                # Set 0.5 for Pool for Warning
                details_db_values["poolstatus"] = 0.5
            else:
                # Set 1.0 for Pool is OK
                details_db_values["poolstatus"] = 1.


            for att in self.localAttribs:
                theId = att
                if theId in thePoolInfo[pool]:
                    theVal = thePoolInfo[pool][theId]
                    self.sumInfo[theId] += theVal
                    if self.unit == 'GB':
                        details_db_values[theId] = float(round(theVal))
                    else:
                        details_db_values[theId] = float(round(theVal,2))
                else:
                    details_db_values[theId] = -1
                    details_db_values["poolstatus"] = 0.

            if details_db_values["poolstatus"] == 0.5:
                self.sumInfo['poolwarning'] +=1
            elif details_db_values["poolstatus"] == 0.:
                self.sumInfo['poolcritical'] +=1





            # store the values to the database
            Details_DB_Class(**details_db_values)

	# unlock the database access
	self.lock.release()


        for att in self.sumInfo.keys():
            self.db_values[ att ] = int(round(self.sumInfo[att]))

 
        if self.limitExceeded(self.sumInfo,'limit_global_critical') == True:
            self.status = 0.0
        elif self.limitExceeded(self.sumInfo,'limit_global_warning') == True:
            self.status = 0.5
        else:
            self.status = 1.0
            
        self.definition+= "Poolgroup: "+self.poolType+"<br/>"
        self.definition+= self.formatLimits()


    def formatLimits(self):
        theLines = []
        for i in ['limit_global_critical','limit_local_critical','limit_global_warning','limit_local_warning']:
            theLines.append(i+": "+self.getLimitVals(i))


        var = ""
        for line in theLines:
            var+=line+"<br/>"
        return var

    def getLimitVals(self,val):
        limVec = []
        for entry in self.thresholds[val].keys():
            limVec.append(entry+self.thresholds[val][entry])
        return ", ".join(limVec)
        

    def output(self):

        # create output sting, will be executed by a printf('') PHP command
        # all data stored in DB is available via a $data[key] call

        mc = []
        mc.append("<?php")
        # Define sub_table for this module
        mc.append('$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];')

        mc.append('if($data["status"] == 1.){')
        mc.append('$c_flag = "ok";')
        mc.append('}')
        mc.append('elseif($data["status"] == 0.5){')
        mc.append('$c_flag = "warning";')
        mc.append('}')
        mc.append('else{')
        mc.append('$c_flag = "critical";')
        mc.append('}')
      
        #Start with module output
        mc.append("printf('")
        mc.append(' <table class="dCacheInfoPoolTable">')

        #Summary table
    
        for att in self.globalSummary:
            mc.append("  <tr>")
            mc.append("    <td>"+self.poolAttribNames[att]['webname']+"</td>")
            mc.append("""    <td>'.$data["""+'"'+ att +'"'+ """].'</td>""")
            mc.append("   </tr>")

        for att in self.globalRatios:
            entry = att.split("/")
            mc.append("  <tr>")
            mc.append("    <td>"+self.poolAttribNames[att]['webname']+"</td>")
            mc.append("""    <td>'.round(($data["""+'"'+ entry[0] +'"'+ """]/$data["""+'"'+ entry[1] +'"'+ """])*100,1).'</td>""")
            mc.append("   </tr>")

            
        
        mc.append("  </table>")
        mc.append(" <br/>")


        # Show/Hide details table
        mc.append(""" <input type="button" value="show/hide results" onfocus="this.blur()" onclick="show_hide(""" + "\\\'" + self.__module__+ "_result\\\'" + """);" />""")
        mc.append(""" <div class="dCacheInfoPoolDetailedInfo" id=""" + "\\\'" + self.__module__+ "_result\\\'" + """ style="display:none;">""")

        mc.append(' <table class="dCacheInfoPoolTableDetails">')
        mc.append("  <tr>")
        mc.append('   <td class="dCacheInfoPoolTableDetails1RowHead">Poolname</td>')
        for att in self.localAttribs:
            mc.append('   <td class="dCacheInfoPoolTableDetailsRestRowHead">'+self.poolAttribNames[att]["webname"]+"</td>")
        for att in self.localRatios:
            mc.append('   <td class="dCacheInfoPoolTableDetailsRestRowHead">'+self.poolAttribNames[att]["webname"]+"</td>")

        mc.append("  </tr>")
     

        mc.append("');") 
        mc.append("foreach ($dbh->query($details_db_sqlquery) as $sub_data)")
        mc.append(" {")

        mc.append('  if($sub_data["poolstatus"] == 1.){')
        mc.append('    $c_flag = "ok";')
        mc.append('  }')
        mc.append('  else{')
        mc.append('    $c_flag = "poolwarning";')
        mc.append('  }')

        mc.append("  printf('")
        mc.append("   <tr class=\"'.$c_flag.'\">")
        mc.append("""    <td class="dCacheInfoPoolTableDetails1Row">'.$sub_data["poolname"].'</td>""")
        for att in self.localAttribs:
            mc.append("""    <td class="dCacheInfoPoolTableDetailsRestRow">'.$sub_data["""+'"'+ att +'"'+ """].'</td>""")
        for entry in self.localRatios:
            att = entry.split("/")
            mc.append("""    <td class="dCacheInfoPoolTableDetailsRestRow">'.round(($sub_data["""+'"'+ att[0] +'"'+ """]/$sub_data["""+'"'+ att[1] +'"'+ """])*100,1).'</td>""")
            
        mc.append("   </tr>")
        mc.append("  ');")
        mc.append(" }")

        mc.append("printf('")
        mc.append(" </table>")
        mc.append(" </div>")
        mc.append("');")
        mc.append("?>")


        
        # export content string
        module_content = ""
        for i in mc:
            module_content +=i+"\n"

        return self.PHPOutput(module_content)