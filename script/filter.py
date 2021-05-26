#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import sys
import copy

def split_predefined(lines):
    line_max_num = len(lines)

    predefined_lines = []
    syntax_lines = []

    isCommentLine = False
    linenum = 0
    last_col = 0
    predefined_line = ""
    syntax_line = ""
    line = lines[linenum]
    while True:
        comment_start_col = -1
        comment_end_col = -1

        if not isCommentLine:
            comment_start_col = line[last_col:].find("/*")
            if comment_start_col != -1:
                comment_start_col += last_col
                isCommentLine = True
        if isCommentLine:
            comment_end_col = line[last_col:].find("*/") # /*/에 대해서 고려 필요.
            if comment_end_col != -1:
                comment_end_col += last_col + 2
        else:
            comment_start_col = line[last_col:].find("//")
            if comment_start_col != -1:
                comment_start_col += last_col
       
        if comment_start_col == -1 and comment_end_col != -1: #comment line
            predefined_line += line[last_col:comment_end_col]
            last_col = comment_end_col if len(line) > comment_end_col else 0
            isCommentLine = False
        elif comment_start_col != -1 and comment_end_col != -1:
            syntax_line += line[last_col:comment_start_col]
            predefined_line += line[comment_start_col:comment_end_col]
            last_col = comment_end_col if len(line) > comment_end_col else 0
            isCommentLine = False
        elif comment_start_col != -1 and comment_end_col == -1:
            syntax_line += line[last_col:comment_start_col]
            predefined_line += line[comment_start_col:]
            last_col = 0
        elif comment_start_col == -1 and comment_end_col == -1:
            if isCommentLine:
                predefined_line += line[last_col:]
            else:
                syntax_line += line[last_col:]
            last_col = 0
        else: #abnormal
            pass

        if last_col == 0:
            predefined_lines.append(predefined_line)
            syntax_lines.append(syntax_line)
            linenum += 1
            if len(lines) <= linenum:
                break
            predefined_line = ""
            syntax_line = ""
            line = lines[linenum]
    return predefined_lines, syntax_lines

def scan(filename):
    NORMAL_LINE = 1
    COMMENT_LINE = 2

    lines = []
    state = NORMAL_LINE
    f = open(filename, 'r')
    while True:
        line = f.readline()
        if not line: break
        lines.append(line.strip('\n'))
    f.close()

    predefined_lines = []
    syntax_lines = []
    predefined_lines , syntax_lines = split_predefined(lines)
    return lines, predefined_lines, syntax_lines

def getCommentRange(linenum, predefined_lines):
    endnum = -1

    startnum = linenum
    while True:
        if startnum <= 0:
            break
        if predefined_lines[startnum].find('/*') != -1:
            break
        if predefined_lines[startnum].find('//') != -1:
            break
        startnum -= 1
    
    endnum = linenum
    while True:
        if endnum >= len(predefined_lines):
            break
        if predefined_lines[endnum].find('*/') != -1:
            break
        elif predefined_lines[endnum].find('//') != -1:
            break
        endnum += 1
    return startnum, endnum

def getCloseBraceLine(linenum, syntax_lines):
    endnum = linenum
    if syntax_lines[endnum].find('}') != -1:
        return endnum

    endnum += 1
    while True:
        if syntax_lines[endnum].find('{') != -1: # 하위 block
            endnum = getCloseBraceLine(endnum, syntax_lines) + 1
            continue
        if syntax_lines[endnum].find('}') != -1:
            break
        endnum += 1
    return endnum

def getSyntaxLineRange(linenum, syntax_lines):
    startnum = linenum
    while True:
        if startnum <= 0:
            break
        tmpline = syntax_lines[startnum - 1].strip()
        if len(tmpline) == 0:
            break
        if tmpline[-1] == '\\' or tmpline[-1] == ',':
            startnum -= 1
        else:
            break

    endnum = linenum
    while True:
        if endnum >= len(syntax_lines):
            break
        tmpline = syntax_lines[endnum].strip()
        if tmpline[-1] == '{':
            endnum = getCloseBraceLine(endnum, syntax_lines)
        if tmpline[-1] == '\\' or tmpline[-1] == ',':
            endnum += 1
        else:
            break
    return startnum, endnum

def processTODO(predefined_lines, syntax_lines, origlines):
    lines = copy.deepcopy(origlines)
    linenum = 0
    line_max_num = len(lines)
    end_linenum = -1
    while linenum < line_max_num:
        tmp = predefined_lines[linenum].find("@NODESCRIPTION")
        if tmp != -1:
            p = re.compile('\s*\S')
            tmp = p.match(syntax_lines[linenum])
            if tmp != None: #check inline comment 
                start_linenum, end_linenum = getSyntaxLineRange(linenum, syntax_lines)
                for i in range(start_linenum, end_linenum + 1):
                    lines[i] = ''
                linenum = end_linenum
                start_linenum = -1
                end_linenum = -1
            else:
                start_linenum, end_linenum = getCommentRange(linenum, predefined_lines)
                for i in range(start_linenum, end_linenum + 1):
                    lines[i] = ''
                start_linenum, end_linenum = getSyntaxLineRange(end_linenum+1, syntax_lines)
                for i in range(start_linenum, end_linenum + 1):
                    lines[i] = ''
                linenum = end_linenum
                start_linenum = -1
                end_linenum = -1
        linenum = linenum + 1 if end_linenum == -1 else end_linenum + 1
    return lines

if len(sys.argv) != 3:
  print("옵션을 주지 않고 이 스크립트를 실행하셨군요. len:", len(sys.argv))

lines, predefined_lines, syntax_lines = scan(sys.argv[1])
modlines = processTODO(predefined_lines, syntax_lines, lines)

f = open(sys.argv[2], 'w')
for line in modlines:
    f.write(line + "\n")
f.close()
