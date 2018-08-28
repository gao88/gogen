#-*- coding:utf-8 -*-
import os
import sys
import codecs

class msgid():
    def __init__(self, filepath):
        self.idset = []
        self.filepath = filepath

    def addid(self, idname, msgid):
        self.idset.append((idname, msgid))

    def getidset(self):
        return self.idset

    def writetofile(self):
        try:
            f = open(self.filepath, "w")
            f.write("package util\n\n")
            f.write("const (\n")
            for v in self.idset:
                if v[0] == "" or v[1] == "":
                    continue
                f.write("    " + v[0] + " = " + v[1] + '\n')
            f.write(")\n")
            f.close()
        except IOError as e:
            print(e)

################################################################################
class tblparser():
    def __init__(self, pkg):
        self.cmd = ''
        self.leftcurlybrace = False
        self.clientid = ''
        self.clientitemlist = []
        self.serverid = ''
        self.serveritemlist = []
        self.titemlist = []
        self.rightcurlybrace = False
        self.client = 1
        self.server = 2
        self.nowitempart = 0
        self.istobj = False
        self.pkg = pkg

    def __str__(self):
        ret  = 'cmd: ' + self.cmd + os.linesep
        ret += 'cid: ' + self.clientid + os.linesep
        ret += 'clientitemlist: ' + os.linesep
        for v in self.clientitemlist:
            ret += v[0] + ':' + v[1] + os.linesep
        ret += 'serverid: ' + self.serverid + os.linesep
        ret += 'serveritemlist: ' + os.linesep
        for v in self.serveritemlist:
            ret += v[0] + ':' + v[1] + os.linesep
        return ret

    def getcmdname(self):
        return self.cmd

    def getclientid(self):
        return self.clientid

    def getserverid(self):
        return self.serverid

    def getclientstructname(self):
        return self._get_go_client_structname()

    def getserverstructname(self):
        return self._get_go_server_structname()

    def getpkgname(self):
        return self.pkg
################################################################################
    def _parsetobj(self, line):
        n = len('t:')
        if len(line) < n or line[ : n] != 't:':
            return False
        end = line.find(':', n)
        self.cmd = line[n : end == -1 and len(line) or end]
        self.istobj = True
        return True
    
    def _parsecmd(self, line):
        line = line.replace(' ', '')
        n = len('cmd:')
        if len(line) < n or line[:n] != 'cmd:':
            return False
        end = line.find(':', n)
        self.cmd = line[n : end == -1 and len(line) or end]
        return True

################################################################################
    def _parsecurlybrace(self, line, tag, saveType):
        n = len(tag)
        if len(line) < n or line[ : n] != tag:
            return False
        if saveType == self.client:
            self.leftcurlybrace = (line[0] == tag)
        elif saveType == self.server:
            self.rightcurlybrace = (line[0] == tag)
        return (line[0] == tag)
    
    def _parseleftcurlybrace(self, line):
        return self._parsecurlybrace(line, '{', self.client)

    def _parserightcurlybrace(self, line):
        return self._parsecurlybrace(line, '}', self.server)
    
################################################################################
    def _parseid(self, line, tag, saveType):
        line = line.replace(' ', '')
        n = len(tag)
        if len(line) < n or line[ : n] != tag:
            return False
        if saveType == self.client:
            self.clientid = line[n : ]
            self.nowitempart = self.client
        elif saveType == 2:
            self.serverid = line[n : ]
            self.nowitempart = self.server
        return True
    
    def _parseclientid(self, line):
        return self._parseid(line, 'c:', self.client)
    
    def _parseserverid(self, line):
        return self._parseid(line, 's:', self.server)
    
################################################################################
    def _csharplisttogo(self, data):
        if len(data) < len('List<>'):
            return data
        if data[:len('List<')] == 'List<' and data[-1] == '>':
            data = '[]' + data[len('List<'):-1]
        return data

    def _csharptypetogo(self, data):
        typereplace = [('int', 'int32'), ('float', 'float32'), ('long', 'uint64'), ('[]int', '[]int32'), ('[]float', '[]float32'), ('[]long', '[]uint64'), ('bool', 'int8'), ('short', 'int16'), ('byte', 'uint8')]
        for v in typereplace:
            if data == v[0]:
                return v[1]
        return data

    def _structtypeconver(self, data):
        if self._isstruct(data) == True:
            if data[:2] == '[]':
                return '[]*' + data[2:]
            else:
                return '*' + data
        return data
    
    def _parseitem(self, line, save):
        firstcolon = line.find(':')
        if firstcolon == -1:
            return False
        itemname = line[ : firstcolon].strip()
        secondcolon = line.find(':', firstcolon + 1)
        if secondcolon == -1:
            secondcolon = len(line)
        itemtype = line[firstcolon + 1: secondcolon].strip()
        itemtype = self._csharplisttogo(itemtype)
        itemtype = self._csharptypetogo(itemtype)
        itemtype = self._structtypeconver(itemtype)
        save.append((itemname, itemtype))
        return True
    
    def _parseclientitem(self, line):
        return self._parseitem(line, self.clientitemlist)

    def _parseserveritem(self, line):
        return self._parseitem(line, self.serveritemlist)

    def _parsetitem(self, line):
        return self._parseitem(line, self.titemlist)

################################################################################
    def parse(self, line):
        ncommand = line.find('//')
        if ncommand != -1:
            line = line[:ncommand]
        line = line.encode('utf-8')
        if line[:3] == codecs.BOM_UTF8:
            line = line[3:]
        line = line.decode('utf-8')
        line = line.strip(' \t\r\n')
        if len(line) < 1:
            return
        if self._parsetobj(line) == True:
            return
        if self._parsecmd(line) == True:
            return
        if self._parseleftcurlybrace(line) == True:
            return
        if self._parseclientid(line) == True:
            return
        if self._parseserverid(line) == True:
            return
        if self.nowitempart == self.client:
            if self._parseclientitem(line) == True:
                return
        if self.nowitempart == self.server:
            if self._parseserveritem(line) == True:
                return
        if self.istobj == True:
            if self._parsetitem(line) == True:
                return
        if self._parserightcurlybrace(line) == True:
            if self.leftcurlybrace == True:
                return True
            else:
                return False

################################################################################
    def _islist(self, data):
        n = len('[]')
        if len(data) > n and data[:n] == '[]':
            return True

    def _isstring(self, data):
        if data == 'string':
            return True

    def _isstruct(self, data):
        if len(data) < 1:
            return
        if self._islist(data) == True:
            data = data[len('[]'):]
        if data[0] == '*':
            data = data[1:]
        if data not in ['byte', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'int', 'float32', 'float64', 'complex64', 'complex128', 'string', 'bool']:
            return True

    def _structnamebytype(self, data):
        if len(data) < 1:
            return
        if self._islist(data) == True:
            data = data[len('[]'):]
        if data[0] == '*':
            data = data[1:]
        return data

    #go begin
    def _gen_go_begin(self):
        gobegin = 'package ' + self.pkg + '\n\n'
        gobegin += 'import (\n'
        gobegin += '    "bytes"\n'
        gobegin += '    "fmt"\n'
        if len(self.clientitemlist) != 0 or len(self.serveritemlist) != 0 or len(self.titemlist) != 0:
            gobegin += '    "encoding/binary"\n'
            gobegin += '    "Core/logger"\n'
        gobegin += ')\n\n'
        return gobegin

    def _get_go_client_structname(self):
        return 'C' + self.cmd

    def _get_go_server_structname(self):
        return 'S' + self.cmd

    def _get_go_structname(self):
        return self.cmd[0].upper() + self.cmd[1:]

    #go struct
    def _gen_go_struct(self, gostructname, itemlist):
        gostruct = 'type ' + gostructname + ' struct {\n'
        for v in itemlist:
            gostruct += '    ' + v[0] + ' ' + v[1] + '\n'
        gostruct += '}\n\n'
        return gostruct

    #go string function
    def _gen_go_string_func(self, gostructname, itemlist):
        gostringfunc = 'func (this *' + gostructname + ') String() string {\n'
        gostringfunc += '    return fmt.Sprintf("'
        for v in itemlist:
            gostringfunc += v[0] + ': %v\\n'
        gostringfunc += '", '
        for v in itemlist:
            gostringfunc += 'this.' + v[0] + ', '
        gostringfunc = gostringfunc[:-2] + ')\n'
        gostringfunc += '}\n\n'
        return gostringfunc

    #go new function
    def _gen_go_new_func(self, gostructname, itemlist):
        gonewfunc = 'func New' + gostructname + '('
        for v in itemlist:
            gonewfunc += v[0] + ' ' + v[1] + ', '
        end = len(itemlist) > 0 and -2 or len(gonewfunc)
        gonewfunc = gonewfunc[:end] + ') *' + gostructname + ' {\n'
        gonewfunc += '    inst := new(' + gostructname + ')\n'
        for v in itemlist:
            gonewfunc += '    inst.' + v[0] + ' = ' + v[0] + '\n'
        gonewfunc += '    return inst\n'
        gonewfunc += '}\n\n'
        return gonewfunc

    #go marshal function
    def _gen_go_marshal_func(self, gostructname, itemlist):
        gomarshal = 'func (this *' + gostructname + ') Marshal() (retBuf *bytes.Buffer, err error) {\n'
        gomarshal += '    retBuf = new(bytes.Buffer)\n'
        for v in itemlist:
            if self._islist(v[1]) == True or self._isstring(v[1]) == True:
                gomarshal += '    err = binary.Write(retBuf, binary.LittleEndian, int16(len(this.' + v[0] + ')))\n'
                gomarshal += '    if err != nil {\n'
                gomarshal += '        logger.Error(err)\n'
                gomarshal += '        return retBuf, err\n'
                gomarshal += '    }\n\n'
            expand = 1
            if self._islist(v[1]) == True and self._isstruct(v[1]) == True:
                gomarshal += '    for i := 0; i < len(this.' + v[0] + '); i++ {\n'
                expand = 2
            if self._isstruct(v[1]) == True:
                bufname = v[0] + 'RetBuf'
                listitem = expand == 1 and v[0] or v[0] + '[i]'
                gomarshal += '    '*expand + bufname + ', err := this.' + listitem + '.Marshal()\n'    #should it support import ???
                gomarshal += '    '*expand + 'if err != nil {\n'
                gomarshal += '    '*expand + '    logger.Error(err)\n'
                gomarshal += '    '*expand + '    return retBuf, err\n'
                gomarshal += '    '*expand + '}\n\n'
                gomarshal += '    '*expand + 'err = binary.Write(retBuf, binary.LittleEndian, ' + bufname + '.Bytes())\n'
                gomarshal += '    '*expand + 'if err != nil {\n'
                gomarshal += '    '*expand + '    logger.Error(err)\n'
                gomarshal += '    '*expand + '    return retBuf, err\n'
                gomarshal += '    '*expand + '}\n'
                if self._islist(v[1]) == True:
                    gomarshal += '    }\n'
                continue
            if self._isstring(v[1]) == True:
                gomarshal += '    err = binary.Write(retBuf, binary.LittleEndian, []byte(this.' + v[0] + '))\n'
                gomarshal += '    if err != nil {\n'
                gomarshal += '        logger.Error(err)\n'
                gomarshal += '        return retBuf, err\n'
                gomarshal += '    }\n\n'
                continue
            gomarshal += '    err = binary.Write(retBuf, binary.LittleEndian, this.' + v[0] + ')\n'
            gomarshal += '    if err != nil {\n'
            gomarshal += '        logger.Error(err)\n'
            gomarshal += '        return retBuf, err\n'
            gomarshal += '    }\n\n'
        gomarshal += '    return\n'
        gomarshal += '}\n\n'
        return gomarshal

    #go unmarshal function
    def _gen_go_unmarshal_func(self, gostructname, itemlist):
        gounmarshal = 'func (this *' + gostructname + ') Unmarshal(retBuf *bytes.Buffer) (err error) {\n'
        for v in itemlist:
            countname = ''
            islist = self._islist(v[1])
            if islist == True or self._isstring(v[1]) == True:
                countname = v[0] + 'Count'
                gounmarshal += '    var ' + countname + ' int16\n'
                gounmarshal += '    err = binary.Read(retBuf, binary.LittleEndian, &' + countname + ')\n'
                gounmarshal += '    if err != nil {\n'
                gounmarshal += '        logger.Error(err)\n'
                gounmarshal += '        return err\n'
                gounmarshal += '    }\n'
            expand = 1
            if islist == True:
                if self._isstruct(v[1]):
                    gounmarshal += '    this.' + v[0] + ' = make(' + v[1] + ', 0, '+ countname + ')\n'
                else:
                    gounmarshal += '    this.' + v[0] + ' = make(' + v[1] + ', '+ countname + ')\n'
                if self._isstruct(v[1]) == True:
                    gounmarshal += '    for i := 0; int16(i) < ' + countname + '; i++ {\n'
                    expand = 2
            if self._isstruct(v[1]) == True:
                structname = self._structnamebytype(v[1])
                if islist == True:
                    gounmarshal += '    '*expand + 'tmp := &' + structname + '{}\n'
                    gounmarshal += '    '*expand + 'err = tmp.Unmarshal(retBuf)\n'
                else:
                    gounmarshal += '    '*expand + 'this.' + v[0] + ' = &' + structname + '{}\n'
                    gounmarshal += '    '*expand + 'err = this.' + v[0] + '.Unmarshal(retBuf)\n'
                gounmarshal += '    '*expand + 'if err != nil {\n'
                gounmarshal += '    '*expand + '    logger.Error(err)\n'
                gounmarshal += '    '*expand + '    return err\n'
                gounmarshal += '    '*expand + '}\n'
                if islist == True:
                    gounmarshal += '    '*expand + 'this.' + v[0] + ' = append(this.' + v[0] + ', tmp)\n'
                    gounmarshal += '    }\n'
                continue
            if self._isstring(v[1]) == True:
                stringbytename = v[0] + 'ByteList'
                gounmarshal += '    ' + stringbytename + ' := make([]byte, ' + countname + ')\n'
                gounmarshal += '    err = binary.Read(retBuf, binary.LittleEndian, &' + stringbytename + ')\n'
                gounmarshal += '    if err != nil {\n'
                gounmarshal += '        logger.Error(err)\n'
                gounmarshal += '        return err\n'
                gounmarshal += '    }\n'
                gounmarshal += '    this.' + v[0] + ' = string(' + stringbytename + ')\n\n'
                continue
            gounmarshal += '    err = binary.Read(retBuf, binary.LittleEndian, &this.' + v[0] + ')\n'
            gounmarshal += '    if err != nil {\n'
            gounmarshal += '        logger.Error(err)\n'
            gounmarshal += '        return err\n'
            gounmarshal += '    }\n\n'
        gounmarshal += '    return nil\n'
        gounmarshal += '}\n\n'
        return gounmarshal

    def _gen_go_get_func(self, gostructname, itemlist):
        goget = ''
        for v in itemlist:
            itemname = v[0]
            goget += 'func (this *' + gostructname + ') Get' + itemname[0].upper() + itemname[1:] + '() ' + v[1] + '{\n'
            goget += '    return this.' + v[0] + '\n'
            goget += '}\n\n'
        return goget

    def _gen_go_set_func(self, gostructname, itemlist):
        goset = ''
        for v in itemlist:
            itemname = v[0]
            goset += 'func (this *' + gostructname + ') Set' + itemname[0].upper() + itemname[1:] + '(v ' + v[1] + ') {\n'
            goset += '    this.' + v[0] + ' = v\n'
            goset += '}\n\n'
        return goset
    
    def gengo(self, filename):
        try:
            f = open(filename, 'w', encoding='utf-8')

            gobegin = self._gen_go_begin()
            if self.istobj == True:
                gostruct = self._gen_go_struct(self._get_go_structname(), self.titemlist)
                gostringfunc = self._gen_go_string_func(self._get_go_structname(), self.titemlist)
                gonewfunc = self._gen_go_new_func(self._get_go_structname(), self.titemlist)
                gomarshalfunc = self._gen_go_marshal_func(self._get_go_structname(), self.titemlist)
                gounmarshalfunc = self._gen_go_unmarshal_func(self._get_go_structname(), self.titemlist)
                gogetfunc = self._gen_go_get_func(self._get_go_structname(), self.titemlist)
                gosetfunc = self._gen_go_set_func(self._get_go_structname(), self.titemlist)

                f.write(gobegin)
                f.write(gostruct)
                f.write(gostringfunc)
                f.write(gonewfunc)
                f.write(gomarshalfunc)
                f.write(gounmarshalfunc)
                f.write(gogetfunc)
                f.write(gosetfunc)
            else:
                goclientstruct = self._gen_go_struct(self._get_go_client_structname(), self.clientitemlist)
                goclientstringfunc = self._gen_go_string_func(self._get_go_client_structname(), self.clientitemlist)
                goclientnewfunc = self._gen_go_new_func(self._get_go_client_structname(), self.clientitemlist)
                goclientmarshalfunc = self._gen_go_marshal_func(self._get_go_client_structname(), self.clientitemlist)
                goclientunmarshalfunc = self._gen_go_unmarshal_func(self._get_go_client_structname(), self.clientitemlist)
                goclientgetfunc = self._gen_go_get_func(self._get_go_client_structname(), self.clientitemlist)
                goclientsetfunc = self._gen_go_set_func(self._get_go_client_structname(), self.clientitemlist)
            
                goserverstruct = self._gen_go_struct(self._get_go_server_structname(), self.serveritemlist)
                goserverstringfunc = self._gen_go_string_func(self._get_go_server_structname(), self.serveritemlist)
                goservernewfunc = self._gen_go_new_func(self._get_go_server_structname(), self.serveritemlist)
                goservermarshalfunc = self._gen_go_marshal_func(self._get_go_server_structname(), self.serveritemlist)
                goserverunmarshalfunc = self._gen_go_unmarshal_func(self._get_go_server_structname(), self.serveritemlist)
                goservergetfunc = self._gen_go_get_func(self._get_go_server_structname(), self.serveritemlist)
                goserversetfunc = self._gen_go_set_func(self._get_go_server_structname(), self.serveritemlist)
                
                f.write(gobegin)
                f.write(goclientstruct)
                f.write(goclientstringfunc)
                f.write(goclientnewfunc)
                f.write(goclientmarshalfunc)
                f.write(goclientunmarshalfunc)
                f.write(goclientgetfunc)
                f.write(goclientsetfunc)

                f.write('/'*90+'\n')
                
                f.write(goserverstruct)
                f.write(goserverstringfunc)
                f.write(goservernewfunc)
                f.write(goservermarshalfunc)
                f.write(goserverunmarshalfunc)
                f.write(goservergetfunc)
                f.write(goserversetfunc)
            f.close()
        except IOError as e:
            print(e)

################################################################################
def genonefile(filename):
    try:
        if filename.find(':') == -1:
            fullpath = os.getcwd() + os.sep + filename
        dirname, ext = os.path.splitext(filename)
        if ext != '.txt':
            return
        newdir = os.getcwd() + os.sep + dirname.lower()
        if os.path.exists(newdir) == False:
            os.makedirs(newdir)
        utildir = os.getcwd() + os.sep + "util"
        if os.path.exists(utildir) == False:
            os.makedirs(utildir)
        f = open(fullpath, encoding='utf-8')
        alllines = f.readlines()
        parser = tblparser(dirname.lower())
        msgidset = msgid(utildir + os.sep + dirname.lower() + "id.go")
        for line in alllines:
            ret = parser.parse(line)
            if ret == True:
                msgidset.addid(parser.getclientstructname(), parser.getclientid())
                msgidset.addid(parser.getserverstructname(), parser.getserverid())
                #msgidset.addid((parser.getpkgname() + '_' + parser.getclientstructname()).upper(), parser.getclientid())
                #msgidset.addid((parser.getpkgname() + '_' + parser.getserverstructname()).upper(), parser.getserverid())
                gofilepath = newdir + os.sep + parser.getcmdname() + '.pb.go'
                print("generate", gofilepath)
                parser.gengo(gofilepath)
                parser = tblparser(dirname.lower())
            elif ret == False:
                raise SyntaxError(filename + " format error")
        f.close()
        msgidset.writetofile()
    except IOError as e:
        print(e)
    except SyntaxError as e:
        print(e)

################################################################################
class enumidfile():
    def __init__(self):
        self.idset = []
        
    def addid(self, idname, msgid):
        self.idset.append((idname, msgid))

    def parsefile(self, filepath):
        try:
            f = open(filepath)
            alllines = f.readlines()
            lefttag = 'const ('
            righttag = ')'
            islefttag = False
            for line in alllines:
                line = line.strip()
                if line == lefttag:
                    islefttag = True
                    continue
                if line == righttag:
                    break
                if islefttag == True:
                    splitret = line.split('=')
                    idname, msgid = splitret[0].strip(), splitret[1].strip()
                    self.addid(idname, msgid)
                    continue
                    
            f.close()
        except IOError as e:
            print(e)

    def writetofile(self, filepath):
        v1set = []
        for v in self.idset:
            v1set.append(v[1])
        v1setlen = len(v1set)
        for i in range(0, v1setlen):
            lastv = v1set[len(v1set) - 1]
            v1set = v1set[:-1]
            if lastv in v1set:
                print("error:", lastv, "is repeat")
        
        try:
            f = open(filepath, "w")
            f.write("package util\n\n")
            f.write("const (\n")
            for v in self.idset:
                if v[0] == "" or v[1] == "":
                    continue
                f.write("    " + v[0] + " = " + v[1] + '\n')
            f.write(")\n")
            f.close()
        except IOError as e:
            print(e)
            
def genoneidfile(dirpath):
    eif = enumidfile()
    for v in os.listdir(dirpath):
        if v != 'enumid.go':
            eif.parsefile(dirpath + os.sep + v)
    eif.writetofile(dirpath + os.sep + "enumid.go")
        
            
def dologic():
    filename = len(sys.argv) >= 2 and sys.argv[1] or None
    #filename = 'Account.txt'
    if filename == None:
        for v in os.listdir(os.getcwd()):
            genonefile(v)
    else:
        genonefile(filename)
    genoneidfile(os.getcwd() + os.sep + 'util')
	
    print("All job finish!please check any wrong exist")
    input()
    
################################################################################        
if __name__ == "__main__":
    dologic()
