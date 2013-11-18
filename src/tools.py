##### TOOL CODE ################################################################

# read and write the PageProps and FileProps meta-dictionaries
def GetProp(prop_dict, key, prop, default=None):
    if not key in prop_dict: return default
    if type(prop) == types.StringType:
        return prop_dict[key].get(prop, default)
    for subprop in prop:
        try:
            return prop_dict[key][subprop]
        except KeyError:
            pass
    return default
def SetProp(prop_dict, key, prop, value):
    if not key in prop_dict:
        prop_dict[key] = {prop: value}
    else:
        prop_dict[key][prop] = value
def DelProp(prop_dict, key, prop):
    try:
        del prop_dict[key][prop]
    except KeyError:
        pass

def GetPageProp(page, prop, default=None):
    global PageProps
    return GetProp(PageProps, page, prop, default)
def SetPageProp(page, prop, value):
    global PageProps
    SetProp(PageProps, page, prop, value)
def DelPageProp(page, prop):
    global PageProps
    DelProp(PageProps, page, prop)
def GetTristatePageProp(page, prop, default=0):
    res = GetPageProp(page, prop, default)
    if res != FirstTimeOnly: return res
    return (GetPageProp(page, '_shown', 0) == 1)

def GetFileProp(page, prop, default=None):
    global FileProps
    return GetProp(FileProps, page, prop, default)
def SetFileProp(page, prop, value):
    global FileProps
    SetProp(FileProps, page, prop, value)

# the Impressive logo (256x64 pixels grayscale PNG)
LOGO = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x00@\x08\x00\x00\x00\x00\xd06\xf6b\x00\x00\x0b\xf1IDATx\xda\xed[y|OW\x16\x7f\xbf\xfc\x12\x12K\x13\xb1\xc4R\x11\xbbN,c\xadHF\xa8\xd6RK\xa7Cf\x08>\xaa\xed\xa0\xa5\x8a\xd8\xe9Hc\x9dRK\x19'+\
'\xb4b\xd4V{\x8d}\xcd\xa0\x944\xb6PF\xc6RU\x82\xa4\x96HD\xf6\xbc\xfe\xee9\xf7\xdew\xee{?Lc>\x9fL\xe6\xe7\xfe\x11\xf7\x9c\xbb\x9c{\xcf\xbb\xf7\x9c\xef9\xf7G\xd3\x9e\x97\xe7\xa5\xa8\x97\x12#7\xdfN:2\xbc\x98\xab\xee\xbf\xd2\t\x1dJB\t\xd7\xdc\x7f\xe9\xeb:/'+\
'\x13\x9fa\x96\xe0O"\xeb\x16Q\x05\xf4\x12\xfb\xd7\xbf)\xf8$C\xf3u=\xa3C\xd1T\xc0F\xa9\x80\x1b\x05\x9e\xc3\'\x93\x8d\xbfZ4-`\xbaT\xc0\x99\x02O\xd2\n\'(U\x14\x15\xd0X\xee__W\xe0I*\xe6\xb3\xf1?\x17\xc9\x13\xd0\xd5P\xc0\xc7\x05\x9fe\xa6cx~\xbf\x82\x8e\x8e'+\
'\\\xeb(S\x0bI\x01\xef\x19\n\xe8\xf5\x0c\xd3\xbc\xb5u\xedk\x05\x1e|\x8dI\xdfTH\n\x98j(\xa0q!-\xa1x\x1e\x93>\xa3\x90\xa4/\x97\xfb\xcf/, T\x0f\xc4\xbf[H\xd2\xf7J\x05\xfcXXf\xa8\x0b\x88\x0f-$\xe9\xdfI\x05l-,\x05\x0c\x03\xf1\x95\x0bI\xfa\x05\xa9\x80\x91'+\
'\x85\xa5\x80\xf9L\xfaCV+\xe3\xfd\xab\xedG\xf9\xc7a3/\xa7\xec\x92\xa5\xcd\x9c\x9bR\x01\xcd\xfec\xa9\x1e~6\x95\x11\xd4\xc6Q\xeaa\xbd.\xab\x87`\xbd\xc1\x90\xd9_M\xedCv\xe5\xd19b\xf1\xd2\x0fB\xdc\x94\xd1\xbb\x98\xf4ko}\xba\xc7\xb1\x96\xcc3\x7f\xa9c\x92'+\
'\xe6\xcd&l\xe3\xeb\xa8\x15\xeb3k\xd5\xc4v\xb2\xa1\xfc\x07\xdf\xde\xd5\xf5\xa4\xed\x91\xadM#~\xbb\xe4p\x92\x9ewi\xf3\x94\xf6\n\xbb\xda\xbc\x98\xeb\xf9\xfa\xb5\x9d3\xc3\xec\x84\xfbP\xec\xff\x01pC\x98\xb0\xea\nT\x04\xf9U\x05\xf9B\xff\xfd\xc9\xf9\xfa'+\
'\xfd}\xd3^7\xba\xb8\x01\x12\xfe\x14\x89m\xac~\xd1Q\xb1\xf59\x863\xdf\xec!\xc6\x8e\xe2\x81\xd7\xfeJT\xc2%])y\x9f\xab_\xb5;p\x9bhZ\xe8UV\x89\x17\xeb\x9a\x99#\x87\xcc\xf5 \xfd\xcb.\xca\x93\r\xb1\x86\n\xbc"\x1fI\xf6\xbf\xc3\xe5\'\xb0K\xe6\x0e\xa0OZ '+\
'\xe18X\xd4KH\xb8\x8f1\x90\xf3Z\x89|\xab\x01\xfd\x1e\x12\t\xac\xbeM\xd3\x02b\x8c=\xa1\x06\xda\x1a\xa7-\xf97\x86\x00\xf7\x1c\xddTn7\xa2\x0b\x18\xc3av\xdd\xfb:Q@\xcb+t\xc4\xd1\x17e\xf7\xcaI\xca\\\x87\xf9\xf1\xf0:\xab\xb0\xcf\x8b\x8fRF\xb2F\x01\xbd'+\
'\xc0\xec\x0fJ\xdfe\x9c\xd5\xfcx\x9f\xa6\x93\\\x08\xe4}\xda\x01\x89@\xc8\x9e\xc5\xea\xb3\xb4\xb04\xd2\xf3\xe7\n\x8e\x86\xa8<\xc2\xd9mH\xa8\xa1[\xca\xfd\x96d\x05K\x18\'Q+\xcb\x0f\n* $M\x1d\x91\\\x81\xf7\xb6\xed5\xcd\x15O\x0c\r)\x99\xbc\x7f\x80'+\
'\xe44\x07:\x1c\xea~\x86\xf8\x89\x8c\xce\xc5X\xbf\xceMu\x92\x87\\\x03\x03\x81\xc2\x8bS\x1d\x9d\xfa\xbb\xb0\xdb\xeb\xbbn`\xcf\xf1\x9a\xdbj\xf6o\xce\xd9\x1d\x89\xc8\xe9(\xef\x0f"\x91Ss\xfe\xe8_;l\xeayl\xbdEVp\x801\xfe\xe9q\x90n(\x08\xf7\x9f\xb1k\xc6'+\
'\xb8u8\xe1\xe7\xbc\xf7\x87\xbc\xdb\x9dTE\x01\x1d\xc5E\xbfgR@C\xb1\x99T;Y\x7f7\xc3\x02\xc1\x80\x15\xd8\x86\xbb\xc9\x8d\x993j\x05\x1e\xc0=F$\xa0g\xe3\x04\xafA\xc3&\xf6g}s\x9bf\x8b\x04\xfa\xa0\xb6\x90\xadw\xaec_\xf6E\xc0Y..\xc0W(?\x80[\xf5Y\x10W\xe9{'+\
'\r\x05\x80\xddX\xb4\x94~Qo\xb4%G\xe0\xbb\x94\xde\x0c\xabj\x80\xbdOA\xcb\x02\x7f\xcd\xdet\xd8\xa6t\xa9\x00\x94\xb2\xae\x9ef\x0b\x1c\xb8\xea\x0eQ\xc0\xef\xc4\xbc;9\xe36#\x8c\xc0d\x12L^\x0b\x96\x8a\x90\xe1\\\x0b0\xe7\xb8\r\xb4\x84\x9b\x85\xdds\x94\xf7'+\
'\xc5\x84\xd9C\x90q\x1c\x889\xacGm`x&\xc3\xe2\xb9\x80\xc5\xd8;KZ\xa5W\xc0\xa2\xea\x9d\x05\xed\t\x1aa\xe1\xc2\x95\xd9\x1d\xab\x84\xaf\x8e\x91\xf0u\x97\x1b=\xf5\xfbP\x9f\x99t\xfd\xfe_\x0b\x05\xc0\xc9Z/\xee\xfd\xc2<\xa9\x80\xceb\xbd\xa39\x036\xb3_z\xd3'+\
'\x14F.3t\xa1\xc7{\xd1\xaby\xc1\x9dU\xbf\'\x1a\x9c\xc3\xe7K\x14\xd7x\x944Ge9g\x15\x18:\xac\xf7\xe0\x8d\t\xe6\xe8D(H\x0b\x14\xe3\xcfJw\xda\x16\x91\xab\xaf\xa0[\x02\rv\xb5\xbe\tTu\xba\x0c\n\xf0\xcce\xecW$\xbbY\x9cP@\xb8\x98\xfee\xce\x18\r7E|\x8f(\xb8'+\
'\xb85\xc0\x00\x80\xb1N\xa9)\xe6\xf0\xcf\x12G\xc0\x06\xfe\xe53\xe2\x05u\xfd\xae4\xf3=\x85\xd3(.8\xd3\x80\x06\x11U\xef\xeb{/2j;\xc1*x\xbe\xabq\xf2\r>\xfe\xa7*\xb2\xc7v\xd3=\xc5/\xd0\xdd\xb0\xc7\xc1F\x93go\xf6\xb7\n\xb0\xdf!\x9e\xbb?\xaf\x0c\xe2\xd3'+\
'\xa7\xb9+w\x82/\xdf\xf7\x01#\xa2\r\xff\xa0\x0f5\xe6\x80\xadF\xc8\xd9\x87\x12/\xa8\xa7\x1bf\xfc\x0f\xdc\xec\xdb\xd5O\x0c\xc8O\xfb\xbb\x1e\x83)\xa9\xb9\xc4\xec\x0f\x80\x01\x9d8\x15\x81\xe3\xef\x19\x8e\xb36\\\x8a\xcb\x04M\xfd\x831\xc6\x19\x1ey\x93\t'+\
'\xa8i6\x10r\xba\xb8\x15\xd4\x8d\xe1\n\xd8%\xf1B6#\xfb\x93\xa5f\x83}\xf2\x06\xbb\xfb\x80 \xc9\xb9\xc2\xf8\x86\x92K\x8b^0\xbb\xa39\xe1p\x81\xc0\xc1/\xe1\x83\xc2Vr\x0f\x95\xa8\x0c\xedC,I\xaa\x08N-2y\r~,\xf5\x0f5\xd3R\xbe\x84\x9d\xa2O\xd8^\xc6\xb4Op%'+\
'\xfa\x89\x80\xc7\xa6\x03\xc6J\x0e\x18\xad\xc5\x88\xa9R\r\x07\xf36t\x9bc\x8ea\x0e:*\xef@S]\xe2E\xc6\x92n\x1f\x03\xa7!\xe1\x1c\x02\x8c\xc6j\xb3N\x95\xd2Z\x9b\xf7\xa7\x95\x02\xceRN\xed\x03\xeak\xd2~XwZ\x8eA\xe3x$~h\xa2\xee\x93\x9f\xc3{\xaf\x9b\x15'+\
'\xb0\x80\x8f6\x8e\xecg\x86\xf3\x9c\x01\xf6\xd9\x1f\xea\xcb\x9cK\xbd\xe5h\x9a\x0eX\x11\x1f\x96\xda\x03\xb7-\x91\x00&\xef\x11=\x93\xf0\x91V\xb2\xda\x0e\x7f\xa1\xd9Z\x9a\xb9\xc31N\x00\xfe\xcd$\xe8\xdc+\xcb\xf9R\xd0\x8e\xfa\xfe\x84T\x86\x9a_\xb0'+\
'\xc7\xf1\xa4\xc7d5\x0e\xd1VpH\xe3\xae\xbe\x13\xe4\xb2\xe4Hy\x88\x13\x16"\xfb\xb2s\xa9\xcc\x98n 9q\xf4\x82U\x89\x84X\xc6\xf8\x9e\x06d\xd0e\x12\x843\xc2$\xe6\xb8\xd3E\xc5\x117Q\x0c\x10\xd5<\xd2\xdaR\x7f\xd2\t\xd0\x1a\n\x04\xb4L\x89\x07+^\xe3'+\
'\xec}j\xa4\xb1E\xa7\x88\xc6\xc0\x86\xad\x05\xbe\xc9D\x94\xed\xa3?\xfe\x04\x9c6\xdc0z\xc1\x0c\xfa\xbd\xef\x98Op#\x18\xd8[\x90\xeb\x19uEY\x14\x80\xaf\x0b\x1c}C\xef\xbe\x964nb\x82\xb9|\xc1\xdb;\x88\xf8\xeeLm:i}\x01co\x04[\x8d\x03ZP\x1a ;"\x03?'+\
'\xb0\x9c\xf3\xb9\xe5E\xc4m\x91\xcaB\xa84\xc3j\xa0\x87:Of\xc3`\xe3\xaf\x96\xe8N\xb8]\x84n{\xe8\x9a\xd0\xab\x1c\xa0@%\x88\xe6_-F\xc3T\x02/\n\xdc\xdb\x85\xb2+\x1d\xe1\xec\x9c\xc1\x84\x8b\xc8Q\x11\x000v\xa3\xa6\xcd\x86\x8fY\x99\x9e\xbbAN\x1f'+\
'\x05h:\x05\xbc\xe0\x16\xd2\xda\xdc\x92\xf0\x1b\x0b\x1c\x89b\xe0\xc4\xfe\x8dN\x88\xb8}\rM\x17\xd1c;\xfc\xa9\x19\\\xef\xad|\xab\x19AJ\x1aC\x18\xbc|\x92\xff\xae^\x0f\n\xcd\x10\x8c\x840F\xab\xf8\x88\xfa\xe7N0\xf2Mg\xe2B\xa0\xe9\xf7J,\xa8\xa9'+\
'&EI\xf8E\x839\x16\x94\x1f\xb4\x0f\xd7\xcc\x0b\x10,X\xf4\x03\xda\xdcW\xc1IN\x8b-*\x9f\x07\x89JjC\xeb\xcf\xedgf\xf0\x93F\x07#\x9a\x9c\x07\xd6\xbb\xa2\xf2!\x9d&.\xf1H\xd6\'^\x90\x1e\x94\x8f,\t?\xf0\x82q\xaa\xb4\xaet\xc2\x18\x8a\xc5v\xb3\xfa'+\
'I\xda\xfc24\xb7zr\xd2\xaa\x077\x04\x1bL\xa9\xab[\x1cVK+U\xb9k\xdf@\xbb\xda\xc9\x13\xa0\xd0\x90\x0c\x92\xe5q\x9c*\x18\x17\xeeL\xd6\x14\x92SG/\xf8\xaa\xd9\xcd<\xb4$\xe1V\x0b\xaa\x1f\x8cx\xc9b#\xaek\xc4\xfb(\x19\x1a_h\x7f\xfb)i\xbbFW1\xbddJ'+\
'\xb0U9\xae\xd3X+`?\xa4\xac\xba9I\x14\x83\x05L\xaf \x99\x10\xc2E9\x13\xb5\x16\x13\x16P\x06\xd3\xd0\x16\xcaQ\x9a\xc62\xbc\xa0|\x86\x9b\x0c\xcb$\x18\xb5$:\xf2H\x9a.R\x9f\xcd E\xf3\xc9\xd3\x12\x97\xe5b\x9d\xa6z=\xf15\x1c\xe1}\x90H\xab\xa8\x02'+\
'\xe6J\'G\xa4|K\xe3I\xa5\xc0\x0fL\x0e\x11/\x98E\xb1F\xb2\xf9 6R\xfd\xda\x1a\x08vI\xfbt4\xe0>H\xd5r\xf2\xb9!\xd5x\xda\xcd\xd9Zh\xce\xb7\x83\xb1S\xca\x0e\xc8\x97\xc1\xa6\xd7E\xf9(\xa4\xe4U\xff$3>\xc4\xf8\x02\x12\xbcY\xd2\x89\xd0\x14\x02\\\xb7'+\
'\x9bB[~u\xa6\xd1\xdb\xa9\xba\x1d8\x921\xc4\x02\xa1\x9d\x9a\xacx\x045\xed\x0b\x81\xb8>@]EU\xc8#\xc6D\x19\xbft\xb2\xdf\x96\xce\xe4\x8b\xa5\xde&$}\xda8\xaf\x18\xab\xd3\xb9\xfc\x05w:aFXv\xc2\x82\x05\x87)*G\x81D\x82)\xb4\xd5\x9a\xea$\xb6"^\xb0'+\
'\x9c \xef\xd3|\x96\xc3\xedc\xea\xf6\x9cx\xa6\x1b\xe2\xe4\xd1\xa4\x05\xe6\xbc|\xe9\xc1\xfe(\xbd\x1d~\x0c\xcc\xd7\x18\x87o\x1c^\xea\xc4\xae\xaa\x02\x96\xab\xcf\x82\xfa#\xbb\x05\x8b\xebzjY\xc2\xf3\x83/\x93E\xc1\x95\xfd\xfd\xbb\x7f\x16\x08!'+\
'\x0c9\xd9\xe6\x88\tOS\x08\xe1@n+E\xaa\x90$d\x1d\xd4|\xcc\x10\xa7\xd6U\xaec\xba\xe9\xcc!\xa2\x89\x0f\x94\x8c7\x1d\x16\xefE\x1e\x0c\xe7\xce\xf4\xa2G\x8dE\xd5n\xcc\xa0\xad\xe6\xbbi\x92-\x9dl\x1c\x81\xb45\xa8\x80\r\xc8\x9b\xa2H]\t\xbc\xab\xc6^B'+\
'\xcf\x80_\xec#\xd2\xf62\xc1K\x81\xd6\x04s\x92U\xfb\x06\xe2R\xd5\xa7\x01\xbe(\xd6~~\n\n\xce\xed\xae\xe6>\xce\x9a\x14\xd0\x1c\xd5\x941\x82\xcd\xeb\xd9j\x04\xcb\x97\xa6\xb1\x86n\x98\x8c\xd98\xa8\xb6\xe63\x1c\x0c\\\x0e\xebR\x07/\xf4\xce\x88F\xb6'+\
'\x92\xbdo\x1a^t\x8d\xb1\xff,\xe5G\x82#\xd0\x0e\xa91u\xb5\x07\xe8W\xa6\xb1H\xc7\xa3\xe9`@[\x954\r\xb3\x9e/\x10/H\x7f,\x05\xa6#\xd5\xe2\x05\xd7\n\xaa7f\xe9cc\xcf%\xe5\xca\xe3\xf8\x86\xd1;\xc1\x1cI\x10p\xc1"\xa6\xbdq\xd9X;)S\xd8\x98\xe0\xe1\xff'+\
'F\xd2\xbc\x9bC\t"=E\xf6\xa9+\xb8\x04\xbd\x83\xee\xcc\xe7\xf5\x15\x9d\xef\x1d8\xcc\x1fY\xd2D\xb8\x9bL\xbd`M\xf3i=i\xf1\x82\xc2\xc6q\xf5)\xe5.\xc18\x88,-.\xcf-\xda2j&\xa4\xed\xb6\x9a\xb8\xc7!\xca\xf4\x8b\xceU\xd9\x89h?|nHN\x17\xf5\xc5\x91\x89M'+\
'\xf1y\xac\xdee\xd9&\xc2\xdd\xa3\xc4\x0b*\xa1\xedm\xe5{K/\xd8O\xc9\x16\xd0\x92\xb3\xa8\xa2f\x0eM\x07X]\xcf\x8c|e\xd4Q\x81QC\x8fS\xf6%aK\xea\xefT^Q\xda\x08\x1f#\x1e\xa5\x96\x98\xa6?&\x02v\xb5\x0cTS\x11\xff\xean\x13\xe1\xeeJrc/Q\xbf\xac~oy\x1c'+\
'\x83\x95l\x01\xf9\xfa\xcbU\xe4\xf6*p\xdb9q\xbe-\x8e\x19\xa3\xce\x12$m\xeb\xf5\x83\xbc\xd7\x93=\r~\xbbS\xd2\xe7G\x1b\xfe\xa3q<\\Q\x8b\x86\x1d\x81\xe0=g/\xd5\xb5\xc8\x11\xbb\xda\x0f=GqOG\xe1\x1f\xbd\x18\xab+\xe6\x841<\xa9\x8b\xb1\x03\xc7\xa6d'+\
'\x0b2SRR\x92\xce\x1f\xda8\xb9\x95\xdd|\xd6\xd5\xdeJi0~g\xfc\xads\x1b\xa2\xc2\x1b\xab\x98\xc8V3l\xda\xee\xeb\xdfE\x0f3\xa3\xe0\xae\x93\xb6\xfcxj\xc5\xe8\xe6J\xa6\xa8\xd9\xe0\t\xed\xad[\rZ\xbc\xf81\xbf\x98\xaa>l\xcb\x89\x1b\x17\xb7\xcc\xe8\xd7'+\
'\xc2\xe3\xbf\xf1\xd3\x00\xcc\xb3L\xd0\\\xb64\x03\x05\xf4t]\x05\xf4\xfc\x95?\xcd\xf8\xbf+\xe8\xb8}\\W\x01\xf0Fr\xc7u\xf7\x8fAv\xac\x0b+\x00~\xce\xb2\xcau\xf7_\x9a&\x7f\\\xb14\xb6\xbcz\xb8X\t\xb3<J\xb8X\x19gy\xf5p\xb1\xb2\xd4\xf2\xea\xe1b\xe5'+\
'\x90\xe5\xd5\xc3\xc5J\xe2\xb3\xfdW\xa5\xe7\xe5y\xf9\x1f(\xbf\x00\x8e\xf2\xeb\x86\xaa\xb6u\xc1\x00\x00\x00\x00IEND\xaeB`\x82'

# determine the next power of two
def npot(x):
    res = 1
    while res < x: res <<= 1
    return res

# convert boolean value to string
def b2s(b):
    if b: return "Y"
    return "N"

# extract a number at the beginning of a string
def num(s):
    s = s.strip()
    r = ""
    while s[0] in "0123456789":
        r += s[0]
        s = s[1:]
    try:
        return int(r)
    except ValueError:
        return -1

# linearly interpolate between two 8-bit RGB colors represented as tuples
def lerpColor(a, b, t):
    return tuple([min(255, max(0, int(x + t * (y - x) + 0.5))) for x, y in zip(a, b)])

# get a representative subset of file statistics
def my_stat(filename):
    try:
        s = os.stat(filename)
    except OSError:
        return None
    return (s.st_size, s.st_mtime, s.st_ctime, s.st_mode)

# determine (pagecount,width,height) of a PDF file
def analyze_pdf(filename):
    f = file(filename,"rb")
    pdf = f.read()
    f.close()
    box = map(float, pdf.split("/MediaBox",1)[1].split("]",1)[0].split("[",1)[1].strip().split())
    return (max(map(num, pdf.split("/Count")[1:])), box[2]-box[0], box[3]-box[1])

# unescape &#123; literals in PDF files
re_unescape = re.compile(r'&#[0-9]+;')
def decode_literal(m):
    try:
        code = int(m.group(0)[2:-1])
        if code:
            return chr(code)
        else:
            return ""
    except ValueError:
        return '?'
def unescape_pdf(s):
    return re_unescape.sub(decode_literal, s)

# parse pdftk output
def pdftkParse(filename, page_offset=0):
    f = file(filename, "r")
    InfoKey = None
    BookmarkTitle = None
    Title = None
    Pages = 0
    for line in f.xreadlines():
        try:
            key, value = [item.strip() for item in line.split(':', 1)]
        except ValueError:
            continue
        key = key.lower()
        if key == "numberofpages":
            Pages = int(value)
        elif key == "infokey":
            InfoKey = value.lower()
        elif (key == "infovalue") and (InfoKey == "title"):
            Title = unescape_pdf(value)
            InfoKey = None
        elif key == "bookmarktitle":
            BookmarkTitle = unescape_pdf(value)
        elif key == "bookmarkpagenumber" and BookmarkTitle:
            try:
                page = int(value)
                if not GetPageProp(page + page_offset, '_title'):
                    SetPageProp(page + page_offset, '_title', BookmarkTitle)
            except ValueError:
                pass
            BookmarkTitle = None
    f.close()
    if AutoOverview:
        SetPageProp(page_offset + 1, '_overview', True)
        for page in xrange(page_offset + 2, page_offset + Pages):
            SetPageProp(page, '_overview', \
                        not(not(GetPageProp(page + AutoOverview - 1, '_title'))))
        SetPageProp(page_offset + Pages, '_overview', True)
    return (Title, Pages)

# translate pixel coordinates to normalized screen coordinates
def MouseToScreen(mousepos):
    return (ZoomX0 + mousepos[0] * ZoomArea / ScreenWidth,
            ZoomY0 + mousepos[1] * ZoomArea / ScreenHeight)

# normalize rectangle coordinates so that the upper-left point comes first
def NormalizeRect(X0, Y0, X1, Y1):
    return (min(X0, X1), min(Y0, Y1), max(X0, X1), max(Y0, Y1))

# check if a point is inside a box (or a list of boxes)
def InsideBox(x, y, box):
    return (x >= box[0]) and (y >= box[1]) and (x < box[2]) and (y < box[3])
def FindBox(x, y, boxes):
    for i in xrange(len(boxes)):
        if InsideBox(x, y, boxes[i]):
            return i
    raise ValueError

# zoom an image size to a destination size, preserving the aspect ratio
def ZoomToFit(size, dest=None):
    if not dest:
        dest = (ScreenWidth + Overscan, ScreenHeight + Overscan)
    newx = dest[0]
    newy = size[1] * newx / size[0]
    if newy > dest[1]:
        newy = dest[1]
        newx = size[0] * newy / size[1]
    return (newx, newy)

# get the overlay grid screen coordinates for a specific page
def OverviewPos(page):
    return ( \
        int(page % OverviewGridSize) * OverviewCellX + OverviewOfsX, \
        int(page / OverviewGridSize) * OverviewCellY + OverviewOfsY  \
    )

def StopMPlayer():
    global MPlayerProcess, VideoPlaying
    if not MPlayerProcess: return

    # first, ask politely
    try:
        MPlayerProcess.stdin.write('quit\n')
        for i in xrange(10):
            if not(MPlayerProcess.poll() is None):
                MPlayerProcess = None
                VideoPlaying = False
                return
            time.sleep(0.1)
    except:
        pass

    # if that didn't work, be rude
    print >>sys.stderr, "MPlayer didn't exit properly, killing PID", MPlayerProcess.pid
    try:
        if os.name == 'nt':
            win32api.TerminateProcess(win32api.OpenProcess(1, False, MPlayerProcess.pid), 0)
        else:
            os.kill(MPlayerProcess.pid, 2)
        MPlayerProcess = None
    except:
        pass
    VideoPlaying = False

def ClockTime(minutes):
    if minutes:
        return time.strftime("%H:%M")
    else:
        return time.strftime("%H:%M:%S")

def FormatTime(t, minutes=False):
    if minutes and (t < 3600):
        return "%d min" % (t / 60)
    elif minutes:
        return "%d:%02d" % (t / 3600, (t / 60) % 60)
    elif t < 3600:
        return "%d:%02d" % (t / 60, t % 60)
    else:
        ms = t % 3600
        return "%d:%02d:%02d" % (t / 3600, ms / 60, ms % 60)

def SafeCall(func, args=[], kwargs={}):
    if not func: return None
    try:
        return func(*args, **kwargs)
    except:
        print >>sys.stderr, "----- Unhandled Exception ----"
        traceback.print_exc(file=sys.stderr)
        print >>sys.stderr, "----- End of traceback -----"

def Quit(code=0):
    global CleanExit
    if not code:
        CleanExit = True
    StopMPlayer()
    pygame.display.quit()
    print >>sys.stderr, "Total presentation time: %s." % \
                        FormatTime((pygame.time.get_ticks() - StartTime) / 1000)
    sys.exit(code)
