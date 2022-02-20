#!/usr/bin/python
# python script to generate configoptions.cpp and config.doc from config.xml
#
# Copyright (C) 1997-2015 by Dimitri van Heesch.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation under the terms of the GNU General Public License is hereby
# granted. No representations are made about the suitability of this software
# for any purpose. It is provided "as is" without express or implied warranty.
# See the GNU General Public License for more details.
#
# Documents produced by Doxygen are derivative works derived from the
# input used in their production; they are not affected by this license.
#
import xml.dom.minidom
import sys
import re
import textwrap
from xml.dom import minidom, Node

def LogStr(str):
    print(str)
    return str + "\n"

def transformDocs(doc):
    # join lines, unless it is an empty line
    # remove doxygen layout constructs
        # Note: also look at expert.cpp of doxywizard for doxywizard parts
    doc = doc.strip()
    doc = doc.replace("\n", " ")
    doc = doc.replace("\r", " ")
    doc = doc.replace("\t", " ")
    doc = doc.replace("\\&", "&")
    doc = doc.replace("(\\c ", "(")
    doc = doc.replace("\\c ", " ")
    doc = doc.replace("\\b ", " ")
    doc = doc.replace("\\e ", " ")
    doc = doc.replace("\\$", "$")
    doc = doc.replace("\\#include ", "#include ")
    doc = doc.replace("\\#undef ", "#undef ")
    doc = doc.replace("-# ", "\n - ")
    doc = doc.replace(" - ", "\n - ")
    doc = doc.replace("\\sa", "\nSee also: ")
    doc = doc.replace("\\par", "\n")
    doc = doc.replace("@note", "\nNote:")
    doc = doc.replace("\\note", "\nNote:")
    doc = doc.replace("\\verbatim", "\n")
    doc = doc.replace("\\endverbatim", "\n")
    doc = doc.replace("<code>", "")
    doc = doc.replace("</code>", "")
    doc = doc.replace("`", "")
    doc = doc.replace("\\<", "<")
    doc = doc.replace("\\>", ">")
    doc = doc.replace("\\@", "@")
    doc = doc.replace("\\\\", "\\")
    # \ref name "description" -> description
    doc = re.sub('\\\\ref +[^ ]* +"([^"]*)"', '\\1', doc)
    # \ref specials
    # \ref <key> -> description
    doc = re.sub('\\\\ref +doxygen_usage', '"Doxygen usage"', doc)
    doc = re.sub('\\\\ref +extsearch', '"External Indexing and Searching"',
                 doc)
    doc = re.sub('\\\\ref +layout', '"Changing the layout of pages"', doc)
    doc = re.sub('\\\\ref +external', '"Linking to external documentation"',
                 doc)
    doc = re.sub('\\\\ref +doxygen_finetune', '"Fine-tuning the output"',
                 doc)
    doc = re.sub('\\\\ref +formulas', '"Including formulas"', doc)
    # fallback for not handled
    doc = re.sub('\\\\ref', '', doc)
    #<a href="address">description</a> -> description (see: address)
    doc = re.sub('<a +href="([^"]*)" *>([^<]*)</a>', '\\2 (see: \n\\1)', doc)
    # LaTeX name as formula -> LaTeX
    doc = doc.replace("\\f$\\mbox{\\LaTeX}\\f$", "LaTeX")
    # Other formula's (now just 2) so explicitly mentioned.
    doc = doc.replace("\\f$2^{(16+\\mbox{LOOKUP\\_CACHE\\_SIZE})}\\f$",
                      "2^(16+LOOKUP_CACHE_SIZE)")
    doc = doc.replace("\\f$2^{16} = 65536\\f$", "2^16=65536")
    # remove consecutive spaces
    doc = re.sub(" +", " ", doc)
    # a dirty trick to get an extra empty line in Doxyfile documentation.
    # <br> will be removed later on again, we need it here otherwise splitlines
    # will filter the extra line.
    doc = doc.replace("<br>", "\n<br>\n")
    # a dirty trick to go to the next line in Doxyfile documentation.
    # <br/> will be removed later on again, we need it here otherwise splitlines
    # will filter the line break.
    doc = doc.replace("<br/>", "\n<br/>\n")
    #
    doc = doc.splitlines()
    split_doc = []
    for line in doc:
        split_doc += textwrap.wrap(line, 78)
    # replace \ by \\, replace " by \", and '  ' by a newline with end string
    # and start string at next line
    docC = []
    for line in split_doc:
        if (line.strip() != "<br/>"):
            docC.append(line.strip().replace('\\', '\\\\').
                    replace('"', '\\"').replace("<br>", ""))
    return docC


def collectValues(node):
    values = []
    for n in node.childNodes:
        if (n.nodeName == "value"):
            if n.nodeType == Node.ELEMENT_NODE:
                if n.getAttribute('name') != "":
                    if n.getAttribute('show_docu') != "NO":
                        name = "<code>" + n.getAttribute('name') + "</code>"
                        desc = n.getAttribute('desc')
                        if (desc != ""):
                            name += " " + desc
                        values.append(name)
    return values


def addValues(var, node):
    retStr = ""
    for n in node.childNodes:
        if (n.nodeName == "value"):
            if n.nodeType == Node.ELEMENT_NODE:
                name = n.getAttribute('name')
                retStr += LogStr("  %s->addValue(\"%s\");" % (var, name))
    return retStr


def parseHeader(node,objName):
    doc = ""
    retStr = ""
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            if (n.nodeName == "docs"):
                if (n.getAttribute('doxyfile') != "0"):
                    doc += parseDocs(n)
    docC = transformDocs(doc)
    #retStr 
    retStr += LogStr("  %s->setHeader(" % (objName))
    rng = len(docC)
    for i in range(rng):
        line = docC[i]
        if i != rng - 1:  # since we go from 0 to rng-1
          tempStr = LogStr("              \"%s\\n\"" % (line))
        else:
            tempStr = LogStr("              \"%s\"" % (line))
        retStr += tempStr
    
    retStr += LogStr("             );")
    return retStr


def prepCDocs(node):
    type = node.getAttribute('type')
    format = node.getAttribute('format')
    defval = node.getAttribute('defval')
    adefval = node.getAttribute('altdefval')
    doc = "";
    if (type != 'obsolete'):
        for n in node.childNodes:
            if (n.nodeName == "docs"):
                if (n.getAttribute('doxyfile') != "0"):
                    if n.nodeType == Node.ELEMENT_NODE:
                        doc += parseDocs(n)
        if (type == 'enum'):
            values = collectValues(node)
            doc += "<br/>Possible values are: "
            rng = len(values)
            for i in range(rng):
                val = values[i]
                if i == rng - 2:
                    doc += "%s and " % (val)
                elif i == rng - 1:
                    doc += "%s." % (val)
                else:
                    doc += "%s, " % (val)
            if (defval != ""):
                doc += "<br/>The default value is: <code>%s</code>." % (defval)
        elif (type == 'int'):
            minval = node.getAttribute('minval')
            maxval = node.getAttribute('maxval')
            doc += "<br/>%s: %s, %s: %s, %s: %s." % (" Minimum value", minval, 
                     "maximum value", maxval,
                     "default value", defval)
        elif (type == 'bool'):
            if (node.hasAttribute('altdefval')):
              doc += "<br/>%s: %s." % ("The default value is", "system dependent")
            else:
              doc += "<br/>%s: %s." % ("The default value is", "YES" if (defval == "1") else "NO")
        elif (type == 'list'):
            if format == 'string':
                values = collectValues(node)
                rng = len(values)
                for i in range(rng):
                    val = values[i]
                    if i == rng - 2:
                        doc += "%s and " % (val)
                    elif i == rng - 1:
                        doc += "%s." % (val)
                    else:
                        doc += "%s, " % (val)
        elif (type == 'string'):
            if format == 'dir':
                if defval != '':
                    doc += "<br/>The default directory is: <code>%s</code>." % (
                        defval)
            elif format == 'file':
                abspath = node.getAttribute('abspath')
                if defval != '':
                    if abspath != '1':
                        doc += "<br/>The default file is: <code>%s</code>." % (
                            defval)
                    else:
                        doc += "<br/>%s: %s%s%s." % (
                            "The default file (with absolute path) is",
                            "<code>",defval,"</code>")
                else:
                    if abspath == '1':
                        doc += "<br/>The file has to be specified with full path."
            elif format =='image':
                abspath = node.getAttribute('abspath')
                if defval != '':
                    if abspath != '1':
                        doc += "<br/>The default image is: <code>%s</code>." % (
                            defval)
                    else:
                        doc += "<br/>%s: %s%s%s." % (
                            "The default image (with absolute path) is",
                            "<code>",defval,"</code>")
                else:
                    if abspath == '1':
                        doc += "<br/>The image has to be specified with full path."
            else: # format == 'string':
                if defval != '':
                    doc += "<br/>The default value is: <code>%s</code>." % (
                        defval)
        # depends handling
        if (node.hasAttribute('depends')):
            depends = node.getAttribute('depends')
            doc += "<br/>%s \\ref cfg_%s \"%s\" is set to \\c YES." % (
                "This tag requires that the tag", depends.lower(), depends.upper())

    docC = transformDocs(doc)
    return docC;

def parseOption(node):
    # Handling part for Doxyfile
    name = node.getAttribute('id')
    type = node.getAttribute('type')
    format = node.getAttribute('format')
    defval = node.getAttribute('defval')
    adefval = node.getAttribute('altdefval')
    depends = node.getAttribute('depends')
    setting = node.getAttribute('setting')
    orgtype = node.getAttribute('orgtype')
    retStr = ""
    docC = prepCDocs(node);
    if len(setting) > 0:
        retStr += LogStr("#if %s" % (setting))
    retStr += LogStr("  //----")
    if type == 'bool':
        if len(adefval) > 0:
            enabled = adefval
        elif defval == '1':
            enabled = "TRUE"
        else:
            enabled = "FALSE"
        retStr += LogStr("  cb = cfg->addBool(")
        retStr += LogStr("             \"%s\"," % (name))
        rng = len(docC)
        for i in range(rng):
            line = docC[i]
            if i != rng - 1:  # since we go from 0 to rng-1
                retStr += LogStr("              \"%s\\n\"" % (line))
            else:
                retStr += LogStr("              \"%s\"," % (line))
        retStr += LogStr("              %s" % (enabled))
        retStr += LogStr("             );")
        if depends != '':
            retStr += LogStr("  cb->addDependency(\"%s\");" % (depends))
    elif type == 'string':
        retStr += LogStr("  cs = cfg->addString(")
        retStr += LogStr("              \"%s\"," % (name))
        rng = len(docC)
        for i in range(rng):
            line = docC[i]
            if i != rng - 1:  # since we go from 0 to rng-1
                retStr += LogStr("              \"%s\\n\"" % (line))
            else:
                retStr += LogStr("              \"%s\"" % (line))
        retStr += LogStr("             );")
        if defval != '':
            retStr += LogStr("  cs->setDefaultValue(\"%s\");" % (defval.replace('\\','\\\\')))
        if format == 'file':
            retStr += LogStr("  cs->setWidgetType(ConfigString::File);")
        elif format == 'image':
            retStr += LogStr("  cs->setWidgetType(ConfigString::Image);")
        elif format == 'dir':
            retStr += LogStr("  cs->setWidgetType(ConfigString::Dir);")
        elif format == 'filedir':
            retStr += LogStr("  cs->setWidgetType(ConfigString::FileAndDir);")
        if depends != '':
            retStr += LogStr("  cs->addDependency(\"%s\");" % (depends))
    elif type == 'enum':
        retStr += LogStr("  ce = cfg->addEnum(")
        retStr += LogStr("              \"%s\"," % (name))
        rng = len(docC)
        for i in range(rng):
            line = docC[i]
            if i != rng - 1:  # since we go from 0 to rng-1
                retStr += LogStr("              \"%s\\n\"" % (line))
            else:
                retStr += LogStr("              \"%s\"," % (line))
        retStr += LogStr("              \"%s\"" % (defval))
        retStr += LogStr("             );")
        retStr += addValues("ce", node)
        if depends != '':
            retStr += LogStr("  ce->addDependency(\"%s\");" % (depends))
    elif type == 'int':
        minval = node.getAttribute('minval')
        maxval = node.getAttribute('maxval')
        retStr += LogStr("  ci = cfg->addInt(")
        retStr += LogStr("              \"%s\"," % (name))
        rng = len(docC)
        for i in range(rng):
            line = docC[i]
            if i != rng - 1:  # since we go from 0 to rng-1
                retStr += LogStr("              \"%s\\n\"" % (line))
            else:
                retStr += LogStr("              \"%s\"," % (line))
        retStr += LogStr("              %s,%s,%s" % (minval, maxval, defval))
        retStr += LogStr("             );")
        if depends != '':
            retStr += LogStr("  ci->addDependency(\"%s\");" % (depends))
    elif type == 'list':
        retStr += LogStr("  cl = cfg->addList(")
        retStr += LogStr("              \"%s\"," % (name))
        rng = len(docC)
        for i in range(rng):
            line = docC[i]
            if i != rng - 1:  # since we go from 0 to rng-1
                retStr += LogStr("              \"%s\\n\"" % (line))
            else:
                retStr += LogStr("              \"%s\"" % (line))
        retStr += LogStr("             );")
        retStr += addValues("cl", node)
        if depends != '':
            retStr += LogStr("  cl->addDependency(\"%s\");" % (depends))
        if format == 'file':
            retStr += LogStr("  cl->setWidgetType(ConfigList::File);")
        elif format == 'dir':
            retStr += LogStr("  cl->setWidgetType(ConfigList::Dir);")
        elif format == 'filedir':
            retStr += LogStr("  cl->setWidgetType(ConfigList::FileAndDir);")
    elif type == 'obsolete':
        retStr += LogStr("  cfg->addObsolete(\"%s\",ConfigOption::O_%s);" % (name,orgtype.capitalize()))
    if len(setting) > 0:
        retStr += LogStr("#else")
        retStr += LogStr("  cfg->addDisabled(\"%s\");" % (name))
        retStr += LogStr("#endif")
    return retStr


def parseGroups(node):
    name = node.getAttribute('name')
    doc = node.getAttribute('docs')
    setting = node.getAttribute('setting')
    retStr = ""
    if len(setting) > 0:
        retStr += LogStr("#if %s" % (setting))
    retStr += LogStr("%s%s" % ("  //-----------------------------------------",
                    "----------------------------------"))
    retStr += LogStr("  cfg->addInfo(\"%s\",\"%s\");" % (name, doc))
    retStr += LogStr("%s%s" % ("  //-----------------------------------------",
                    "----------------------------------"))
    if len(setting) > 0:
        retStr += LogStr("#endif")
    retStr += LogStr("")
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            retStr += LogStr(parseOption(n))
    return retStr

def parseGroupMapEnums(node):
    retStr = ""
    def escape(value):
        return re.sub(r'[^\w]','_',value)
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            type   = n.getAttribute('type')
            name   = n.getAttribute('id')
            defval = n.getAttribute('defval')
            if type=='enum':
                retStr += LogStr("\nenum class %s_t" % (name))
                retStr += LogStr("{")
                for nv in n.childNodes:
                    if nv.nodeName == "value":
                        value = nv.getAttribute('name')
                        if value:
                            retStr += LogStr("  %s," % (escape(value)))
                retStr += LogStr("};\n")
                retStr += LogStr("inline {0}_t {1}_str2enum(const QCString &s)".format(name,name))
                retStr += LogStr("{")
                retStr += LogStr("  QCString lc = s.lower();")
                retStr += LogStr("  static const std::unordered_map<std::string,{0}_t> map =".format(name))
                retStr += LogStr("  {")
                for nv in n.childNodes:
                    if nv.nodeName == "value":
                        value = nv.getAttribute('name')
                        if value:
                            retStr += LogStr("    {{ \"{0}\", {1}_t::{2} }},".format(value.lower(),name,escape(value)))
                retStr += LogStr("  };")
                retStr += LogStr("  auto it = map.find(lc.str());")
                retStr += LogStr("  return it!=map.end() ? it->second : {0}_t::{1};".format(name,escape(defval)))
                retStr += LogStr("}\n")
                retStr += LogStr("inline QCString {0}_enum2str({1}_t v)".format(name,name))
                retStr += LogStr("{")
                retStr += LogStr("  switch(v)")
                retStr += LogStr("  {")
                for nv in n.childNodes:
                    if nv.nodeName == "value":
                        value = nv.getAttribute('name')
                        if value:
                            retStr += LogStr("    case {0}_t::{1}: return \"{2}\";".format(name,escape(value),value))
                retStr += LogStr("  }")
                retStr += LogStr("  return \"{0}\";".format(defval))
                retStr += LogStr("}")
    return retStr


def parseGroupMapGetter(node):
    retStr = ""
    map = { 'bool':'bool', 'string':'const QCString &', 'int':'int', 'list':'const StringVector &' }
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            setting = n.getAttribute('setting')
            if len(setting) > 0:
                retStr += LogStr("#if %s" % (setting))
            type = n.getAttribute('type')
            name = n.getAttribute('id')
            if type=='enum':
                retStr += LogStr("    %-22s %-30s const                  { return %s(m_%s); }" % (name+'_t',name+'()',name+'_str2enum',name))
                retStr += LogStr("    %-22s %-30s const                  { return m_%s; }" % ('const QCString &',name+'_str()',name))
            elif type in map:
                retStr += LogStr("    %-22s %-30s const                  { return m_%s; }" % (map[type],name+'()',name))
            if len(setting) > 0:
                retStr += LogStr("#endif")
    return retStr

def parseGroupMapSetter(node):
    retStr = ""
    map = { 'bool':'bool', 'string':'const QCString &', 'int':'int', 'list':'const StringVector &' }
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            setting = n.getAttribute('setting')
            if len(setting) > 0:
                retStr += LogStr("#if %s" % (setting))
            type = n.getAttribute('type')
            name = n.getAttribute('id')
            if type=='enum':
                retStr += LogStr("    %-22s update_%-46s { m_%s = %s(v); return v; }" % (name+'_t',name+'('+name+'_t '+' v)',name,name+'_enum2str'))
            elif type in map:
                retStr += LogStr("    %-22s update_%-46s { m_%s = v; return m_%s; }" % (map[type],name+'('+map[type]+' v)',name,name))
            if len(setting) > 0:
                retStr += LogStr("#endif")
    return retStr

def parseGroupMapVar(node):
    retStr = ""
    map = { 'bool':'bool', 'string':'QCString', 'enum':'QCString', 'int':'int', 'list':'StringVector' }
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            setting = n.getAttribute('setting')
            if len(setting) > 0:
                retStr += LogStr("#if %s" % (setting))
            type = n.getAttribute('type')
            name = n.getAttribute('id')
            if type in map:
                retStr += LogStr("    %-12s m_%s;" % (map[type],name))
            if len(setting) > 0:
                retStr += LogStr("#endif")
    return retStr

def parseGroupInit(node):
    retStr = ""
    map = { 'bool':'Bool', 'string':'String', 'enum':'Enum', 'int':'Int', 'list':'List' }
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            setting = n.getAttribute('setting')
            if len(setting) > 0:
                retStr += LogStr("#if %s" % (setting))
            type = n.getAttribute('type')
            name = n.getAttribute('id')
            if type in map:
                retStr += LogStr("  %-25s = ConfigImpl::instance()->get%s(__FILE__,__LINE__,\"%s\");" % ('m_'+name,map[type],name))
            if len(setting) > 0:
                retStr += LogStr("#endif")
    return retStr

def parseGroupMapInit(node):
    retStr = ""
    map = { 'bool':'Bool', 'string':'String', 'enum':'String', 'int':'Int', 'list':'List' }
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            setting = n.getAttribute('setting')
            if len(setting) > 0:
                retStr += LogStr("#if %s" % (setting))
            type = n.getAttribute('type')
            name = n.getAttribute('id')
            if type in map:
                retStr += LogStr("    { %-25s Info{ %-13s &ConfigValues::m_%s }}," % ('\"'+name+'\",','Info::'+map[type]+',',name))
            if len(setting) > 0:
                retStr += LogStr("#endif")
    return retStr

def parseGroupCDocs(node):
    retStr = ""
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            type = n.getAttribute('type')
            name = n.getAttribute('id')
            docC = prepCDocs(n);
            if type != 'obsolete':
                retStr += LogStr("  doc->add(")
                retStr += LogStr("              \"%s\"," % (name))
                rng = len(docC)
                for i in range(rng):
                    line = docC[i]
                    if i != rng - 1:  # since we go from 0 to rng-1
                        retStr += LogStr("              \"%s\\n\"" % (line))
                    else:
                        retStr += LogStr("              \"%s\"" % (line))
                retStr += LogStr("          );")
    return retStr

def parseOptionDoc(node, first):
    # Handling part for documentation
    name = node.getAttribute('id')
    type = node.getAttribute('type')
    format = node.getAttribute('format')
    defval = node.getAttribute('defval')
    adefval = node.getAttribute('altdefval')
    depends = node.getAttribute('depends')
    setting = node.getAttribute('setting')
    doc = ""
    if (type != 'obsolete'):
        for n in node.childNodes:
            if (n.nodeName == "docs"):
                if (n.getAttribute('documentation') != "0"):
                    if n.nodeType == Node.ELEMENT_NODE:
                        doc += parseDocs(n)
        if (first):
            LogStr(" \\anchor cfg_%s" % (name.lower()))
            LogStr("<dl>")
            LogStr("")
            LogStr("<dt>\\c %s <dd>" % (name))
        else:
            LogStr(" \\anchor cfg_%s" % (name.lower()))
            LogStr("<dt>\\c %s <dd>" % (name))
        LogStr(" \\addindex %s" % (name))
        LogStr(doc)
        if (type == 'enum'):
            values = collectValues(node)
            LogStr("")
            LogStr("Possible values are: ")
            rng = len(values)
            for i in range(rng):
                val = values[i]
                if i == rng - 2:
                    LogStr("%s and " % (val))
                elif i == rng - 1:
                    LogStr("%s." % (val))
                else:
                    LogStr("%s, " % (val))
            if (defval != ""):
                LogStr("")
                LogStr("")
                LogStr("The default value is: <code>%s</code>." % (defval))
            LogStr("")
        elif (type == 'int'):
            minval = node.getAttribute('minval')
            maxval = node.getAttribute('maxval')
            LogStr("")
            LogStr("")
            LogStr("%s: %s%s%s, %s: %s%s%s, %s: %s%s%s." % (
                     " Minimum value", "<code>", minval, "</code>", 
                     "maximum value", "<code>", maxval, "</code>",
                     "default value", "<code>", defval, "</code>"))
            LogStr("")
        elif (type == 'bool'):
            LogStr("")
            LogStr("")
            if (node.hasAttribute('altdefval')):
                LogStr("The default value is: system dependent.")
            else:
                LogStr("The default value is: <code>%s</code>." % (
                    "YES" if (defval == "1") else "NO"))
            LogStr("")
        elif (type == 'list'):
            if format == 'string':
                values = collectValues(node)
                rng = len(values)
                for i in range(rng):
                    val = values[i]
                    if i == rng - 2:
                        LogStr("%s and " % (val))
                    elif i == rng - 1:
                        LogStr("%s." % (val))
                    else:
                        LogStr("%s, " % (val))
            LogStr("")
        elif (type == 'string'):
            if format == 'dir':
                if defval != '':
                    LogStr("")
                    LogStr("The default directory is: <code>%s</code>." % (
                        defval))
            elif format == 'file':
                abspath = node.getAttribute('abspath')
                if defval != '':
                    LogStr("")
                    if abspath != '1':
                        LogStr("The default file is: <code>%s</code>." % (
                            defval))
                    else:
                        LogStr("%s: %s%s%s." % (
                            "The default file (with absolute path) is",
                            "<code>",defval,"</code>"))
                else:
                    if abspath == '1':
                        LogStr("")
                        LogStr("The file has to be specified with full path.")
            elif format =='image':
                abspath = node.getAttribute('abspath')
                if defval != '':
                    LogStr("")
                    if abspath != '1':
                        LogStr("The default image is: <code>%s</code>." % (
                            defval))
                    else:
                        LogStr("%s: %s%s%s." % (
                            "The default image (with absolute path) is",
                            "<code>",defval,"</code>"))
                else:
                    if abspath == '1':
                        LogStr("")
                        LogStr("The image has to be specified with full path.")
            else: # format == 'string':
                if defval != '':
                    LogStr("")
                    LogStr("The default value is: <code>%s</code>." % (
                        defval.replace('\\','\\\\')))
            LogStr("")
        # depends handling
        if (node.hasAttribute('depends')):
            depends = node.getAttribute('depends')
            LogStr("")
            LogStr("%s \\ref cfg_%s \"%s\" is set to \\c YES." % (
                "This tag requires that the tag", depends.lower(), depends.upper()))
        return False


def parseGroupsDoc(node):
    retStr = ""
    name = node.getAttribute('name')
    doc = node.getAttribute('docs')
    retStr += LogStr("\section config_%s %s" % (name.lower(), doc))
    # Start of list has been moved to the first option for better
    # anchor placement
    #  LogStr "<dl>"
    #  LogStr ""
    first = True
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            first = parseOptionDoc(n, first)
    if (not first):
        retStr += LogStr("</dl>")
    return retStr


def parseGroupsList(node, commandsList):
    list = ()
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            type = n.getAttribute('type')
            if type != 'obsolete':
                commandsList = commandsList + (n.getAttribute('id'),)
    return commandsList


def parseDocs(node):
    doc = ""
    for n in node.childNodes:
        if n.nodeType == Node.TEXT_NODE:
            doc += n.nodeValue.strip()
        if n.nodeType == Node.CDATA_SECTION_NODE:
            doc += n.nodeValue.rstrip("\r\n ").lstrip("\r\n")
    #doc += "<br>"
    return doc


def parseHeaderDoc(node):
    doc = ""
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            if (n.nodeName == "docs"):
                if (n.getAttribute('documentation') != "0"):
                    doc += parseDocs(n)
    LogStr(doc)
    return doc


def parseFooterDoc(node):
    doc = ""
    for n in node.childNodes:
        if n.nodeType == Node.ELEMENT_NODE:
            if (n.nodeName == "docs"):
                if (n.getAttribute('documentation') != "0"):
                    doc += parseDocs(n)
    return LogStr(doc)


def main():
    if len(sys.argv)<3 or (not sys.argv[1] in ['-doc','-cpp','-wiz','-maph','-maps']):
        sys.exit('Usage: %s -doc|-cpp|-wiz|-maph|-maps config.xml' % sys.argv[0])
    try:
        doc = xml.dom.minidom.parse(sys.argv[2])
    except Exception as inst:
        sys.stdout = sys.stderr
        LogStr("")
        LogStr(inst)
        LogStr("")
        sys.exit(1)
    elem = doc.documentElement
    if (sys.argv[1] == "-doc"):
        f = open("doc.txt", "w")
        f.write(LogStr("/* WARNING: This file is generated!"))
        f.write(LogStr(" * Do not edit this file, but edit config.xml instead and run"))
        f.write(LogStr(" * python configgen.py -doc config.xml to regenerate this file!"))
        f.write(LogStr(" */"))
        # process header
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if (n.nodeName == "header"):
                    f.write(parseHeaderDoc(n))
        # generate list with all commands
        commandsList = ()
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if (n.nodeName == "group"):
                    commandsList = parseGroupsList(n, commandsList)
        f.write(LogStr("\\secreflist"))
        for x in sorted(commandsList):
            f.write(LogStr("\\refitem cfg_%s %s" % (x.lower(), x)))
        f.write(LogStr("\\endsecreflist"))
        # process groups and options
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if (n.nodeName == "group"):
                    f.write(parseGroupsDoc(n))
        # process footers
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if (n.nodeName == "footer"):
                    f.write(parseFooterDoc(n))
        f.close()
    elif (sys.argv[1] == "-maph"):
        f = open("configvalues.h", "w")
        f.write(LogStr("/* WARNING: This file is generated!"))
        f.write(LogStr(" * Do not edit this file, but edit config.xml instead and run"))
        f.write(LogStr(" * python configgen.py -map config.xml to regenerate this file!"))
        f.write(LogStr(" */"))
        f.write(LogStr("#ifndef CONFIGVALUES_H"))
        f.write(LogStr("#define CONFIGVALUES_H"))
        f.write(LogStr(""))
        f.write(LogStr("#include <string>"))
        f.write(LogStr("#include <unordered_map>"))
        f.write(LogStr("#include \"qcstring.h\""))
        f.write(LogStr("#include \"containers.h\""))
        f.write(LogStr("#include \"settings.h\""))
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if n.nodeName == "group":
                    f.write(parseGroupMapEnums(n))
        f.write(LogStr(""))
        f.write(LogStr("class ConfigValues"))
        f.write(LogStr("{"))
        f.write(LogStr("  public:"))
        f.write(LogStr("    static ConfigValues &instance() { static ConfigValues theInstance; return theInstance; }"))
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if n.nodeName == "group":
                    f.write(parseGroupMapGetter(n))
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if n.nodeName == "group":
                    f.write(parseGroupMapSetter(n))
        f.write(LogStr("    void init();"))
        f.write(LogStr("    StringVector fields() const;"))
        f.write(LogStr("    struct Info"))
        f.write(LogStr("    {"))
        f.write(LogStr("      enum Type { Bool, Int, String, List, Unknown };"))
        f.write(LogStr("      Info(Type t,bool         ConfigValues::*b) : type(t), value(b) {}"))
        f.write(LogStr("      Info(Type t,int          ConfigValues::*i) : type(t), value(i) {}"))
        f.write(LogStr("      Info(Type t,QCString     ConfigValues::*s) : type(t), value(s) {}"))
        f.write(LogStr("      Info(Type t,StringVector ConfigValues::*l) : type(t), value(l) {}"))
        f.write(LogStr("      Type type;"))
        f.write(LogStr("      union Item"))
        f.write(LogStr("      {"))
        f.write(LogStr("        Item(bool         ConfigValues::*v) : b(v) {}"))
        f.write(LogStr("        Item(int          ConfigValues::*v) : i(v) {}"))
        f.write(LogStr("        Item(QCString     ConfigValues::*v) : s(v) {}"))
        f.write(LogStr("        Item(StringVector ConfigValues::*v) : l(v) {}"))
        f.write(LogStr("        bool         ConfigValues::*b;"))
        f.write(LogStr("        int          ConfigValues::*i;"))
        f.write(LogStr("        QCString     ConfigValues::*s;"))
        f.write(LogStr("        StringVector ConfigValues::*l;"))
        f.write(LogStr("      } value;"))
        f.write(LogStr("    };"))
        f.write(LogStr("    const Info *get(const QCString &tag) const;"))
        f.write(LogStr("  private:"))
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if (n.nodeName == "group"):
                    f.write(parseGroupMapVar(n))
        f.write(LogStr("};"))
        f.write(LogStr(""))
        f.write(LogStr("#endif"))
        f.close()
    elif (sys.argv[1] == "-maps"):
        f = open("configvalues.cpp", "w")
        f.write(LogStr("/* WARNING: This file is generated!"))
        f.write(LogStr(" * Do not edit this file, but edit config.xml instead and run"))
        f.write(LogStr(" * python configgen.py -maps config.xml to regenerate this file!"))
        f.write(LogStr(" */"))
        f.write(LogStr("#include \"configvalues.h\""))
        f.write(LogStr("#include \"configimpl.h\""))
        f.write(LogStr("#include <unordered_map>"))
        f.write(LogStr(""))
        f.write(LogStr("const ConfigValues::Info *ConfigValues::get(const QCString &tag) const"))
        f.write(LogStr("{"))
        f.write(LogStr("  static const std::unordered_map< std::string, Info > configMap ="))
        f.write(LogStr("  {"))
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if (n.nodeName == "group"):
                    f.write(parseGroupMapInit(n))
        f.write(LogStr("  };"))
        f.write(LogStr("  auto it = configMap.find(tag.str());"))
        f.write(LogStr("  return it!=configMap.end() ? &it->second : nullptr;"))
        f.write(LogStr("}"))
        f.write(LogStr(""))
        f.write(LogStr("void ConfigValues::init()"))
        f.write(LogStr("{"))
        f.write(LogStr("  static bool first = TRUE;"))
        f.write(LogStr("  if (!first) return;"))
        f.write(LogStr("  first = FALSE;"))
        f.write(LogStr(""))
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if (n.nodeName == "group"):
                    f.write(parseGroupInit(n))
        f.write(LogStr("}"))
        f.write(LogStr(""))
        f.write(LogStr("StringVector ConfigValues::fields() const"))
        f.write(LogStr("{"))
        f.write(LogStr("  return {"));
        first=True
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if (n.nodeName == "group"):
                    for c in n.childNodes:
                        if c.nodeType == Node.ELEMENT_NODE:
                            name = c.getAttribute('id')
                            type = c.getAttribute('type')
                            if type!='obsolete':
                                if not first:
                                    f.write(LogStr(","))
                                first=False
                                sys.stdout.write('    "'+name+'"')
        f.write(LogStr(""))
        f.write(LogStr("  };"))
        f.write(LogStr("}"))
    elif (sys.argv[1] == "-cpp"):
        f = open("misc.h", "w");
        f.write(LogStr("/* WARNING: This file is generated!"))
        f.write(LogStr(" * Do not edit this file, but edit config.xml instead and run"))
        f.write(LogStr(" * python configgen.py -cpp config.xml to regenerate this file!"))
        f.write(LogStr(" */"))
        f.write(LogStr(""))
        f.write(LogStr("#include \"configoptions.h\""))
        f.write(LogStr("#include \"configimpl.h\""))
        f.write(LogStr("#include \"portable.h\""))
        f.write(LogStr("#include \"settings.h\""))
        f.write(LogStr(""))
        f.write(LogStr("void addConfigOptions(ConfigImpl *cfg)"))
        f.write(LogStr("{"))
        f.write(LogStr("  ConfigString *cs;"))
        f.write(LogStr("  ConfigEnum   *ce;"))
        f.write(LogStr("  ConfigList   *cl;"))
        f.write(LogStr("  ConfigInt    *ci;"))
        f.write(LogStr("  ConfigBool   *cb;"))
        f.write(LogStr(""))
        # process header
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if (n.nodeName == "header"):
                    f.write(LogStr(parseHeader(n,'cfg')))
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if (n.nodeName == "group"):
                    f.write(LogStr(parseGroups(n)))
        f.write(LogStr("}"))
        f.close()
    elif (sys.argv[1] == "-wiz"):
        f = open("settings.h", "w")
        f.write(LogStr("/* WARNING: This file is generated!"))
        f.write(LogStr(" * Do not edit this file, but edit config.xml instead and run"))
        f.write(LogStr(" * python configgen.py -wiz config.xml to regenerate this file!"))
        f.write(LogStr(" */"))
        f.write(LogStr("#include \"configdoc.h\""))
        f.write(LogStr("#include \"docintf.h\""))
        f.write(LogStr(""))
        f.write(LogStr("void addConfigDocs(DocIntf *doc)"))
        f.write(LogStr("{"))
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if (n.nodeName == "header"):
                    f.write(parseHeader(n,'doc'))
        for n in elem.childNodes:
            if n.nodeType == Node.ELEMENT_NODE:
                if (n.nodeName == "group"):
                    f.write(parseGroupCDocs(n))
        f.write(LogStr("}"))
        f.close()

if __name__ == '__main__':
    main()
