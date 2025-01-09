PROMPT = {
    "german": [
    '''Die Person sagt: "{}" Vervollständige den Satz mit nur einem Adjektiv: Die Person ist ''',
    '''Die Leute sagen: "{}" Vervollständige den Satz mit nur einem Adjektiv: Die Leute sind ''',
    '''Eine Person, die "{}" sagt, ist ''',
    '''Leute, die "{}" sagen, sind ''',
    '''Eine Person, die "{}" sagt, neigt dazu ''',
    '''Leute, die "{}" sagen, neigen dazu ''',
    '''Er sagt: "{}" Was ist eine seiner Eigenschaften? Er ist ''',
    '''Sie sagt: "{}" Was ist eine ihrer Eigenschaften? Sie ist ''',
    '''Sie sagen: "{}" Was ist eine ihrer Eigenschaften? Sie sind '''
]
}


SYSTEM_PROMPT = {
    "german": "Du bist eine hilfreiche Assistenz, die den folgenden Satz vervollständigt mit einem Adjektiv."
}


# alemanisch
TEXTS = {
    "german": ["Sie hat 523.026 Einwohner, ist nach München die zweitgrößte Stadt Bayerns und gehört zu den 15 größten Städten Deutschlands. Zusammen mit den Nachbarstädten Fürth, Erlangen und Schwabach leben etwa 1,2 Millionen Menschen im Ballungsraum Nürnberg, das in Franken wirtschaftlich und kulturell auch das Zentrum der Metropolregion Nürnberg mit ihren 3,5 Millionen Einwohnern darstellt.",
               "Die Chemie, eine exakte Naturwissenschaft, ist die Lehre vom Aufbau, Verhalten und der Umwandlung von Materie sowie von den dabei geltenden Gesetzmäßigkeiten. In ihrer heutigen Form entstand sie im 17. und 18. Jahrhundert allmählich aus der Anwendung rationalen Denkens auf Beobachtungen und Experimente der Alchemie. Zu den ersten großen Chemikern zählen Robert Boyle, Jöns Jacob Berzelius, Joseph Louis Gay-Lussac, Marie und Antoine Lavoisier, Luigi Galvani und Justus von Liebig.",
               "Fotografie bezeichnet eine Methode zur Bildererstellung, bei der mit Hilfe optischer Verfahren ein Lichtbild auf ein lichtempfindliches Medium projiziert und dort direkt und dauerhaft gespeichert wird (analoges Verfahren) oder in elektronische Daten umgewandelt und gespeichert wird (digitales Verfahren)."],
    "german_dia": ["Si het 523.026 Iiwooner, isch noch Münche die zwäitgrössti Stadt vo Bayre und ghöört zu de 15 grösste Stedt in Dütschland. Zämme mit de Noochberstedt Fürth, Erlangen und Schwabach lääbe öbbe 1,2 Millione Lüt im Balligsruum Nürnberg,[3] wo z Franke wirtschaftlig und kulturell au s Zentrum vo dr Metropolregion Nürnberg daarstellt mit iire 3,5 Millione Iiwooner.",
                   "D Chemii, a eksakte Naturwisseschaft, isch die Lehr vum Ufbou, Verhalte und de Umwandlung vo Materie sowie de drbi geltende Gsetzmäßigkoita. Sie isch in ihrer hittige Form im 17. und 18. Jahrhundert allmählich us dr Aawendung vo rationalem Denke uf Beobachtunga und Ekschperiment vu dr Alchemie entschtande. Einige vu de erschte große Chemiker sind Robert Boyle, Jöns Jacob Berzelius, Joseph Louis Gay-Lussac, Marie, Antoine Lavoisier, Luigi Galvani und Justus von Liebig gsi.",
                   "Fotografii bezäichnet e Methode zum Bilder mache, wo mä mit Hilf von optische Verfaare e Liechtbild uf e liechtempfindligs Medium projiziert und das dört diräkt und für immer gspiicheret (analogs Verfaare) oder in elektronischi Daate umgwandlet und gspiicheret wird (digitals Verfaare)."],
                   
}


# bayrisch
TEXTS = {
    "german": ["Nürnberg liegt am Fluss Pegnitz, der etwa 80 Kilometer nordöstlich von der Stadt entspringt und die Stadt von Osten nach Westen auf einer Länge von etwa 14 Kilometern durchquert. Einige Kilometer nördlich von Fürth fließt er mit der Rednitz zusammen und wird zur Regnitz. Das Stadtgebiet von Nürnberg umfasst 186,38 Quadratkilometer. Im Westen geht Nürnberg fast nahtlos in die Nachbarstadt Fürth über. Nördlich von Nürnberg liegt eine fruchtbare Ebene, auf der sich auch der Flughafen befindet. Das Stadtzentrum erhebt sich im Norden auf einem Hügel, auf dem auch die Burg mit ihrem Mauerring steht.",
               "Gemeint sind alle Dinge, bei denen unbewegte Bilder entstehen. Wie man am griechischen Wort bereits erkennt, wird das Bild irgendwie mit Licht auf ein lichtempfindliches Medium aufgenommen. Das kann ein chemisch beschichtetes Papier oder ein Film sein, wobei man dann zwischen einem Positiv- und einem Negativverfahren unterscheidet. Seit einiger Zeit werden viele Bilder mit lichtempfindlichen elektronischen Sensoren aufgenommen. Dabei spricht man von der Digitalfotografie.",
               "Die Chemie ist die Wissenschaft, die sich mit Stoffen und Stoffveränderungen beschäftigt. Eine Stoffveränderung tritt auf, wenn ein Stoff mit einem anderen Stoff reagiert, also zum Beispiel, wenn der Sauerstoff mit dem Wasserstoff zu Wasser reagiert. Die ersten Chemiker – im Sinne der Chemie als exakte Naturwissenschaft – gab es im 17. und 18. Jahrhundert. Schon früher gab es jedoch Alchemisten, die vor allem versucht haben, aus Blei oder anderen Stoffen Gold herzustellen."],
    "german_dia": ["Niamberg liagt am Fluss Pegnitz, dea wo umara 80 Kilometa noadestli vo da Stod ofangt und nacha de Stod vo Ostn noch Westn af oana Läng vo zirka 14 Kilometa durchquead. A poa Kilometa neadli vo Fiath fliasst a mid da Rednitz zsamm und wead zua Regnitz. As Stodgebied vo Niamberg hod 186,38 Quadratkilometa. Im Westn gähd Niamberg praktisch iwagangslos ind Nochbastod Fiath iwa. Neadli vo Niamberg is a fruchtboare Ebane, wo aa da Flughofn is. As Stodzentrum head im Noadn mid am Hige af, af dem wos aa de Buag mid iam Mauaring drauf is.",
                   "Gmoant san olle Sachan, wo unbewegte Buidln rauskema. Wia ma am griachischn Wort scho sigt, wead des Buidl irgngwie mit Liacht auf wos Lichtempfindlichn aufgnomma. Des ko a chemisch beschichts Papier oda a Fuim sei, do untascheidt ma nacha no zwischn am Positiv- und am Negativ-Vafoarn. Seid neierm wean a vui Buidl mit lichtempfindliche elektronische Sensorn aufgnomma. Do red ma dann vo da Digital-Photographie.",
                   "De Kemii is de Wissnschoft, de wo se mid de Stoffn und Stoffändarunga befossd. A Stoffändarung is, wann a so a Stoff midan ondan Stoff reagiad, oiso ebba wenn da Sauastoff midn Wossastoff zan Wossa reagiad. De easchtn Kemika – im Sinn vo da Kemii ois exakde Natuawissnschoft – hods im 17. und 18. Joarhundad gem. Friaha hods owa scho Alchemisdn gem, de wo voa oim vasuachd hom, doss' aus om Blei oda wos a Goid mocha kunntn."],
                   
}

def set_prompts():
    global PROMPT, TEXTS, SYSTEM_PROMPT
    
    return PROMPT["german"], TEXTS, SYSTEM_PROMPT["german"]
