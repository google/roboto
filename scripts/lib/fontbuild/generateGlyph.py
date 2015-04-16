from anchors import alignComponentsToAnchors


def parseComposite(composite):
    c = composite.split("=")
    d = c[1].split("/")
    glyphName = d[0]
    if len(d) == 1:
        offset = [0,0]
    else:
        offset = [int(i) for i in d[1].split(",")]
    accentString = c[0]
    accents = accentString.split("+")
    baseName = accents.pop(0)
    accentNames = [i.split(":") for i in accents ]
    return (glyphName, baseName, accentNames, offset)


def generateGlyph(f,gname):
    glyphName, baseName, accentNames, offset = parseComposite(gname)
    if baseName.find("_") != -1:
        g = f.newGlyph(glyphName)
        for componentName in baseName.split("_"):
            g.appendComponent(componentName, (g.width, 0))
            g.width += f[componentName].width
    else: 
        if not f.has_key(glyphName):
            try:
                f.compileGlyph(glyphName, baseName, accentNames)
            except KeyError as e:
                print ("KeyError raised for composition rule '%s', likely %s "
                    "anchor not found in glyph '%s'" % (gname, e, baseName))
                return
            g = f[glyphName]
            if len(accentNames) > 0:
                alignComponentsToAnchors(f, glyphName, baseName, accentNames)
            if offset[0] != 0 or offset[1] != 0:
                g.width += offset[1] + offset[0]
                g.move((offset[0], 0))
        else:
            print ("Existing glyph '%s' found in font, ignoring composition "
                "rule '%s'" % (glyphName, gname))
