import sys
if not len(sys.argv) > 1:
    print "Specify input file!"
    print 'usage: skinfix.exe infile outfile'
    exit

from xml.etree.ElementTree import ElementTree, Element, fromstring, parse

elegantohd = """<foo>
  <output id="0">
    <resolution xres="1280" yres="720" bpp="32" />
  </output>
  <colors>
    <color name="background" value="#2518252e" />
    <color name="background1" value="#25080808" />
    <color name="background2" value="#2538454e" />
    <color name="background3" value="#2548555e" />
    <color name="black" value="#00000000" />
    <color name="blue" value="#000064c7" />
    <color name="dark" value="#00062748" />
    <color name="foreground" value="#00ffffff" />
    <color name="green" value="#00389416" />
    <color name="grey" value="#00aaaaaa" />
    <color name="listback" value="#254f7497" />
    <color name="menu" value="#00062748" />
    <color name="red" value="#00f23d21" />
    <color name="transparent" value="#ffffffff" />
    <color name="transpBlack" value="#80000000" />
    <color name="transpWhite" value="#80ffffff" />
    <color name="un15000000" value="#15000000" />
    <color name="un1b2c47" value="#001b2c47" />
    <color name="un232a33" value="#00232a33" />
    <color name="un25062748" value="#25062748" />
    <color name="un25344452" value="#25344452" />
    <color name="un333333" value="#00333333" />
    <color name="un343c4f" value="#00343c4f" />
    <color name="un38435a" value="#0038435a" />
    <color name="un45ffffff" value="#45ffffff" />
    <color name="un808888" value="#00808888" />
    <color name="un9f1313" value="#009f1313" />
    <color name="unbbbbbb" value="#00bbbbbb" />
    <color name="uncccccc" value="#00cccccc" />
    <color name="undcaaaa" value="#00dcaaaa" />
    <color name="undcdcdc" value="#00dcdcdc" />
    <color name="une5b243" value="#00e5b243" />
    <color name="unff000000" value="#ff000000" />
    <color name="white" value="#00ffffff" />
    <color name="yellow" value="#00bab329" />
    <color name="yellow1" value="#00cc9329" />
  </colors>
  <windowstyle type="skinned" id="0">
    <title offset="210,14" font="Regular;27" />
    <color name="Background" color="background" />
    <color name="LabelForeground" color="white" />
    <color name="ListboxBackground" color="background" />
    <color name="ListboxForeground" color="white" />
    <color name="ListboxSelectedBackground" color="un25344452" />
    <color name="ListboxSelectedForeground" color="white" />
    <color name="ListboxMarkedBackground" color="un25344452" />
    <color name="ListboxMarkedForeground" color="green" />
    <color name="ListboxMarkedAndSelectedBackground" color="un25344452" />
    <color name="ListboxMarkedAndSelectedForeground" color="red" />
    <color name="WindowTitleForeground" color="white" />
    <color name="WindowTitleBackground" color="un232a33" />
    <borderset name="bsWindow">
      <pixmap pos="bpTopLeft" filename="Elgato-HD/b_tl.png" />
      <pixmap pos="bpTop" filename="Elgato-HD/b_t.png" />
      <pixmap pos="bpTopRight" filename="Elgato-HD/b_tr.png" />
      <pixmap pos="bpLeft" filename="Elgato-HD/b_l.png" />
      <pixmap pos="bpRight" filename="Elgato-HD/b_r.png" />
      <pixmap pos="bpBottomLeft" filename="Elgato-HD/b_bl.png" />
      <pixmap pos="bpBottom" filename="Elgato-HD/b_b.png" />
      <pixmap pos="bpBottomRight" filename="Elgato-HD/b_br.png" />
    </borderset>
  </windowstyle>
  <windowstyle type="skinned" id="1">
    <color name="Background" color="black" />
    <color name="LabelForeground" color="white" />
    <color name="ListboxBackground" color="black" />
    <color name="ListboxForeground" color="white" />
    <color name="ListboxSelectedBackground" color="black" />
    <color name="ListboxSelectedForeground" color="white" />
    <color name="ListboxMarkedBackground" color="black" />
    <color name="ListboxMarkedForeground" color="white" />
    <color name="ListboxMarkedAndSelectedBackground" color="black" />
    <color name="ListboxMarkedAndSelectedForeground" color="white" />
    <color name="WindowTitleForeground" color="white" />
    <color name="WindowTitleBackground" color="black" />
  </windowstyle>
  <fonts>
    <font filename="nmsbd.ttf" name="Regular" scale="95" />
    <font filename="lcd.ttf" name="LCD" scale="100" />
    <font filename="ae_AlMateen.ttf" name="Replacement" scale="90" replacement="1" />
    <font filename="tuxtxt.ttf" name="Console" scale="100" />
    <font filename="/usr/share/enigma2/Elgato-HD/num.ttf" name="Num" scale="100" />
  </fonts>
  </foo>
"""

infile = open(sys.argv[1])
main = parse(infile).getroot()

header = fromstring(elegantohd)

root = Element("skin")
map(root.append, header)
root.append(main)

if len(sys.argv) > 2:
    outfile = sys.argv[2]
else:
    outfile = 'skin.xml'
    from os.path import exists
    if exists(outfile):
        from shutil import copy
        copy(outfile, outfile+'.backup')

tree = ElementTree(root)        
tree.write(outfile)
