#======================================================================================
# IHM de saisie d'info
#  Usage:
#    dialog=Zdialog(title,margin,spacing)
#    vbox=dialog.area
#    ( insertion box et wdigets   ...)
#    result=dialog.Run()
#
#
#======================================================================================
try:
    import gi
except:
    print("\n********* Le package python3-gi  doit être installé ! ************")
    exit()


gi.require_version("Gtk", "3.0")

from gi.repository import Gtk,Gdk

#========================== Boxes / Label sans id / value ========================

#---------------------------------------------------------
# usage interne , pour Zhbox , Zvbox
#---------------------------------------------------------
def Zfbox(hostbox,orientation,spacing=10,border=0,title="" ):
        # creation d'un cadre
        if border > 0 :
            frame = Gtk.Frame(label=title)
            frame.set_border_width(0)   
            frame.set_label_align(0,1) # texte exactement au dessus du cadre
            hostbox.pack_start(frame, True, False, 10)

        # creation de la box, rattachée soit au cadre soit au hostbox
        box=Gtk.Box(orientation=orientation, spacing=spacing)
        box.set_border_width(border)
        if border > 0 : frame.add(box)
        else:           hostbox.pack_start(box, True, False, 0)
        return box

#---------------------------------------------------------
# Boite à placement horizontal
# - si border >  0 elle est entourée d'un cadre , avec une marge interne "border" et un titre "title"
# - les objets à l'intérieur sont séparés par "spacing"
#---------------------------------------------------------
def Zhbox(hostbox,spacing=10,border=0,title=""):
        return Zfbox(hostbox,Gtk.Orientation.HORIZONTAL, spacing,border,title)

#---------------------------------------------------------
# Boite à placement vertical
# - si border >  0 elle est entourée d'un cadre , avec une marge interne "border" et un titre "title"
# - les objets à l'intérieur sont séparés par "spacing"
#---------------------------------------------------------
def Zvbox(hostbox,spacing=10,border=0,title=""):
        return Zfbox(hostbox,Gtk.Orientation.VERTICAL, spacing,border,title)

#---------------------------------------------------------
# Texte inerte
#---------------------------------------------------------
def Ztext(hostbox,title):
        label=Gtk.Label(label=title)
        hostbox.pack_start(label, True, False, 0)
        return label

# future use...
class Zcell():

    def __init__(self,hostbox,col,row,width,height):
        
        self.vbox=Gtk.Box()
        hostbox.attach(self.vbox,col,row,width,height)

#========================== Objets avec une valeur  ========================
# ces objets ont un "id" , une valeur "value"  et sont rattachés à un "owner" de type Zdialog
# ils s'enregistrent auprès du Zdialog
# quand Zdialog termine, il appelle leur fonction "Getvalue" pour fabriquer un resultat { id : value ,.... }
# 
# ils sont affichés dans une Boite "hostbox" , obtenue 
# - soit par Zdialog.area
# - soit par Zvbox , Zhbox
#==========================================================================

#---------------------------------------------------
# bouton qui provoque 
# - la fin du Zdialog si action=None
# - le lancement de action(owner,id) sinon
#
# - sa valeur finale est soit "" , soit son id s'il a été cliqué
#
# la technique pour changer la couleur est une usine à gaz, qui fait appel à une CSS
#  - on associe une classe CSS "button-ID" au bouton
#  - on crée une CSS qui définit la couleur pour cette classe
# avant, il existait modify_bg() , mais ça devait être trop simple ...
#---------------------------------------------------
class Zbutton():

    def __init__(self,owner,hostbox,id,title,color="grey",action=None):
        self.owner=owner
        self.owner.Register(id,self)

        self.value=""
        self.id=id
        self.action=action

        self.button = Gtk.Button(label=title)

        # Associe une classe CSS au bouton, et ajoute cette classe dans la feuille de style
        self.button.get_style_context().add_class(f"button-{id}")  
        self.apply_css(id,color)

        self.button.connect("clicked", self.on_button_clicked)
        hostbox.pack_start(self.button, True, False, 0)

    def Getvalue(self):
        return self.value

    # cliquer le bouton provoque la sortie si action=None, ou lance cette action
    def on_button_clicked(self, widget):
        self.value=self.id
        if self.action is None:
            self.owner.Exit()
        else:
            self.action(self.owner,self.id)

    # Créer et appliquer la CSS 
    def apply_css(self,id,color):
 
        css = f"""
.button-{id} {{
            background-color: {color};
            border: 2px solid black;
}}
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css.encode('UTF-8') )  # la CSS doit être un Byte array
        Gtk.StyleContext.add_provider_for_screen(  Gdk.Screen.get_default(), style_provider,  Gtk.STYLE_PROVIDER_PRIORITY_USER  )


#---------------------------------------------------
# Champ de saisie avec un label , et un contenu initial
# - si position = "up" le label est au dessus, sinon il est à gauche
#
#---------------------------------------------------
class Zentry():

    def __init__(self,owner, hostbox,id,titre,position,initvalue=""):
        self.id=id
        owner.Register(id,self)

        if position == "up" :
            position=Gtk.Orientation.VERTICAL
        else:
            position=Gtk.Orientation.HORIZONTAL

        box=Gtk.Box(orientation=position, spacing=2)
        hostbox.pack_start(box, True, False, 0)
        label=Gtk.Label(label=titre)
        label.set_justify(Gtk.Justification.LEFT)
        self.entry=Gtk.Entry()
        self.entry.set_text(initvalue)
        box.pack_start(label, False, False, 0)
        box.pack_start(self.entry, False, False, 0)
         
    def Getvalue(self):
        return self.entry.get_text()

#---------------------------------------------------
# Check button avec un label , et un contenu initial
#
#---------------------------------------------------
class Zcheck():

    def __init__(self,owner, hostbox,id,titre,initvalue=""):
        self.id=id
        owner.Register(id,self)

        self.check=Gtk.CheckButton(label=titre)
        self.check.connect("toggled", self.on_button_toggled, id)
        hostbox.pack_start(self.check, True, False, 0)
        if initvalue=="":
            self.check.set_active(False)
        else:
            self.check.set_active(True)    

    def Getvalue(self):
        s= self.check.get_active()
        if s : return "on"
        else : return ""

    def on_button_toggled(self, widget,id):
        xxx=True


#---------------------------------------------------
# Liste de choix , avec un titre 
# - "items" : tableau des valeurs possibles
# - default : indice de l'élément pré-sélectionné ( commence à 0 !! )  . Si -1, pas de présélection
#
# Sa valeur est le texte sélectionné
#---------------------------------------------------
class Zlistbox( ):

    def __init__(self,owner,hostbox, id,title,items,default=-1):

        owner.Register(id,self)

        self.listbox = Gtk.ListBox()
        self.value=""
        
        # Ajout des éléments
        for item in items:
            zlabel = Gtk.Label(label=item)
            zrow = Gtk.ListBoxRow()
            zrow.add(zlabel)
            self.listbox.add(zrow)


        self.listbox.connect("row-activated", self.on_item_selected)

       # Création d'un cadre autour de la ListBox  
        frame = Gtk.Frame(label=title)
        frame.set_border_width(1)  # Largeur de la bordure  
        frame.set_label_align(0,1) 
        frame.add(self.listbox)

        # Ajout du conteneur à la fenêtre  
        # le 1e True répartit les widgets sur l'espace disponible , le 2e True aggrandit les widget
        hostbox.pack_start(frame,True,False,0)

        # Sélectionner l'élément par défaut  
        if default >= 0:
            self.listbox.select_row(self.listbox.get_row_at_index(default))
            self.value=items[default]

    def Getvalue(self):
        return self.value

    def on_item_selected(self, widget, row):
        # Récupérer le label de l'élément sélectionné 
        label = row.get_child().get_label()
        self.value = label


#===============================================================
# Boite de dialogue dans laquelle on rajoute des widgets, ayant chacun un id (string), et renvoyant une valeur
#
# A la sortie, on récupère un dictionnary { id : value .... }
#
# On sort par 2 méthodes
# - cliquer sur un bouton
# - cliquer sur la croix : dans ce cas, toutes les valeurs existent mais sont vides
#
# Si belongsto est une Zdialog , alors la boite est modeless
#================================================================
class Zdialog():

    #--------------------------------------------------------------------------
    # Initilisation
    # Crée self.area qui est une box, dans laquelle les widgets seront installés
    # - margin: espace entre la fenêtre et la box 
    # - spacing: les widgets dans la box, seront espacés de "spacing"
    #--------------------------------------------------------------------------
    def __init__(self,title,margin=30,spacing=10,belongsto=None):


        self.values={}
        self.widgets={}
        #self.set_default_size(200,2500)
        #self.set_position( Gtk.WindowPosition.CENTER_ALWAYS )

        # creer la fenetre principale ou une sous-boite non-modale
        if belongsto is None:
            self.root= Gtk.Window(title=title)
            self.modeless=False
            self.drawzone=self.root
        else:
            self.root= Gtk.Dialog(title="My Dialog", transient_for=belongsto.root)
            self.drawzone=self.root.get_content_area()
            self.modeless=True


        self.area= Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)
        #vbox.set_margin_top(100) #vbox.set_margin_bottom(100) #vbox.set_margin_right(200) #vbox.set_margin_left(200)
        self.area.set_border_width(margin)
        self.drawzone.add(self.area)

    # appelé par chaque widget, pour que Zdialog soit capable d'enregistrer sa valeur au moment de sortir
    # initialise self.values[id]="" pour chaque widget
    def Register(self,id, widget):
        self.widgets[id]=widget
        self.values[id]=""
        return widget

    # appelle tous les widgets enregistrés pour récupérer leur valeur
    def Getvalues(self):
        values={}
        for id,widget in self.widgets.items():
            values[id] = widget.Getvalue()
        return values

    #--------------------------------------------------------------------------
    # Appelé par un bouton, pour provoquer la sortie, et récupérer  les données
    #--------------------------------------------------------------------------
    def Exit(self):
        # sauver les valeurs avant de tout détruire
        self.values=self.Getvalues()
        # sans ça, la fenêtre reste jusqu'à la fin du programme python ...
        # note: ça supprime la fenêtre graphique, mais pas l'objet python...
        self.root.destroy() 
        # provoque la sortie de Gtk.main()
        if not self.modeless: Gtk.main_quit()

    #--------------------------------------------------------------------------
    # Affichage du Zdialog, et attente de sortie
    # renvoie la liste des valeurs 
    #--------------------------------------------------------------------------
    def Run(self):
        if not self.modeless:
            self.root.connect("destroy", Gtk.main_quit)
            self.root.show_all()
            Gtk.main()
        else:
            self.root.show_all()  
  
        #print (self.values)
        return self.values



