# File: voom_mode_html.py
# Last Modified: 2017-01-07
# Description: VOoM -- two-pane outliner plugin for Python-enabled Vim
# Website: http://www.vim.org/scripts/script.php?script_id=2657
# Author: Vlad Irnov (vlad DOT irnov AT gmail DOT com)
# License: CC0, see http://creativecommons.org/publicdomain/zero/1.0/

"""
VOoM markup mode for PHP headings.
See |voom-mode-php|,  ../../../doc/voom.txt#*voom-mode-php*

trait ApiTestTrait
{
    public function assertApiResponse(Array $actualData)
    {
        $this->assertApiSuccess();

        $response = json_decode($this->response->getContent(), true);
        $responseData = $response['data'];

        $this->assertNotEmpty($responseData['id']);
        $this->assertModelData($actualData, $responseData);
    }

    public function assertApiSuccess()
    {
        $this->assertResponseOk();
        $this->seeJson(['success' => true]);
    }

    public function assertModelData(Array $actualData, Array $expectedData)
    {
        foreach ($actualData as $key => $value) {
            $this->assertEquals($actualData[$key], $expectedData[$key]);
        }
    }
}
"""

import sys
if sys.version_info[0] > 2:
        xrange = range

import re
headline_search = re.compile(r'<\s*h(\d+).*?>(.*?)</h(\1)\s*>', re.IGNORECASE).search
class_search = re.compile(r'^\s*(class|trait)\s*(\w*)[^\w\s\{]?', re.I | re.M).search
method_search = re.compile(r'^\s*(public|private|protected)?\s*function\s*(\w*)[^\(\w\s\{]?', re.I | re.M).search


def hook_makeOutline(VO, blines):
    """Return (tlines, bnodes, levels) for Body lines blines.
    blines is either Vim buffer object (Body) or list of buffer lines.
    """
    Z = len(blines)
    tlines, bnodes, levels = [], [], []
    tlines_add, bnodes_add, levels_add = tlines.append, bnodes.append, levels.append
    for i in xrange(Z):
        bline = blines[i]
        if not ('class' in bline or 'function' in bline or 'trait' in bline):
            continue

        classMatch = class_search(bline)
        methodMatch = method_search(bline)
        if not classMatch and not methodMatch:
            continue

        if classMatch:
            lev = 1
            head = classMatch.group(0)
        elif methodMatch:
            lev = 2
            head = methodMatch.group(2)
        # delete all html tags
        tline = '  %s|%s' %('. '*(lev-1), head.strip())
        tlines_add(tline)
        bnodes_add(i+1)
        levels_add(lev)
    return (tlines, bnodes, levels)


def hook_newHeadline(VO, level, blnum, tlnum):
    """Return (tree_head, bodyLines).
    tree_head is new headline string in Tree buffer (text after |).
    bodyLines is list of lines to insert in Body buffer.
    """
    tree_head = 'NewHeadline'
    if level == 1:
        bodyLines = ["class %s\n{\n}" %(tree_head), '']
    else:
        bodyLines = ["function %s () {\n}" %(tree_head), '']
    return (tree_head, bodyLines)

def hook_doBodyAfterOop(VO, oop, levDelta, blnum1, tlnum1, blnum2, tlnum2, blnumCut, tlnumCut):
    # this is instead of hook_changeLevBodyHead()
    #print('oop=%s levDelta=%s blnum1=%s tlnum1=%s blnum2=%s tlnum2=%s tlnumCut=%s blnumCut=%s' % (oop, levDelta, blnum1, tlnum1, blnum2, tlnum2, tlnumCut, blnumCut))
    Body = VO.Body
    Z = len(Body)

    ind = get_body_indent(VO.body)
    # levDelta is wrong when pasting because hook_makeOutline() looks at relative indent
    # determine level of pasted region from indent of its first line
    if oop=='paste':
        bline1 = Body[blnum1-1]
        lev = int((len(bline1) - len(bline1.lstrip())) / len(ind)) + 1
        levDelta = VO.levels[tlnum1-1] - lev

    if not levDelta: return

    indent = abs(levDelta) * ind
    #--- copied from voom_mode_thevimoutliner.py -----------------------------
    if blnum1:
        assert blnum1 == VO.bnodes[tlnum1-1]
        if tlnum2 < len(VO.bnodes):
            assert blnum2 == VO.bnodes[tlnum2]-1
        else:
            assert blnum2 == Z

    # dedent (if possible) or indent every non-blank line in Body region blnum1,blnum2
    blines = []
    for i in xrange(blnum1-1,blnum2):
        line = Body[i]
        if not line.strip():
            blines.append(line)
            continue
        if levDelta > 0:
            line = '%s%s' %(indent,line)
        elif levDelta < 0 and line.startswith(indent):
            line = line[len(indent):]
        blines.append(line)

    # replace Body region
    Body[blnum1-1:blnum2] = blines
    assert len(Body)==Z


