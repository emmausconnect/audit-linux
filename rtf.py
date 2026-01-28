#####################################################################
# Generation de qrcode
#
#####################################################################
import os

# On se protege contre le cas où le module qrcode n'est pas installé
try:
    import qrcode

    #--------------------------------------------------------------
    # Transforme un texte en qrcode
    #  fabrique le fichier .png  filename
    # renvoie le contenu en hexadecimal du fichier, pour qu'il soit inséré dans un document RTF
    #---------------------------------------------------------------
    def MakeQR( txt , filename ):

        # fabrique le qrcode
        qr = qrcode.QRCode( version=6, error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=10, border=4 )
        qr.add_data(txt)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(filename)

        # relit le fichier .png
        with open( filename, "rb" ) as f:
            data=f.read()
        
        # renvoie le contenu hexadecimal
        out=""
        for b in data:
            out=out + f'{b:02X}'

        return out

except:
    def MakeQR(txt,filename):
        return ""

#--------------------------------------------------------------
# Encode les caracteres speciaux, pour insertion dans du .rtf
#  
#---------------------------------------------------------------
def RtfEncode( txt ):
    out=""
    for c in txt:
        index=ord(c)
        if c in "\\{}" :
            out=out+ "\\" + c
        elif index >= 128:
            out = out + f"{{\\u{index}}}"  # generer {\u233}  avec des {} , sinon pb de separation
        else:
            out=out+ c
            
    return out

#--------------------------------------------------------------
# Fabrique une mini fiche .rtf, incluant un qrcode
#
# La strucutre RTF est simplifiée au maximum !
#
# INPUT
#  items:      tableau de triplet ( taille police , label , valeur ) contenantles infos à afficher 
#  txtqrcode:  le texte à mettre dans un qrcode
#  filertf:    fichier .rtf à générer
#---------------------------------------------------------------
def MakeRTF( items, txtqrcode ,filertf , tmpdir ):

    # squelette minimaliste de fiche
    # les zones @ITEMDATA@ @PNGDATA@ seront à remplacer
    template=r"""{\rtf1\ansi\deff3\adeflang1025
{\fonttbl{\f0\froman\fprq2\fcharset0 Times New Roman;}}
\ltrch\hich\af0\loch\fs36\b
@ITEMDATA@

\par
\par {\pict\picscalex26\picscaley26\pngblip
@PNGDATA@
}

\par 
}
"""

    # fabrication du contenu @ITEMDATA@
    itemdata=""
    for item in items:
        (size,label,value) = item
        size=size*2  # conversion pour que size soit exprimé en points
        if label != "": label = f"{label:<12}"
        itemdata=itemdata+ f"\\par\\fs{size} {label}" + RtfEncode(value) + "\n"
 
    # fabrication du contenu @PNGDATA@
    pngdata= MakeQR( txtqrcode , os.path.join(tmpdir , "qrcode.png") )

    # insertion
    rtftxt=template
    rtftxt=rtftxt.replace("@PNGDATA@",pngdata)
    rtftxt=rtftxt.replace("@ITEMDATA@",itemdata)

    # génération fichier
    with open( filertf,"w") as f:
        f.write(rtftxt)

    


