from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from enigma import eTimer, eDVBResourceManager, quitMainloop
from Components.NimManager import nimmanager, InitNimManager
from Components.Sources.FrontendStatus import FrontendStatus
from Components.TuneTest import Tuner
from Components.TunerInfo import TunerInfo
from Components.ConfigList import ConfigListScreen
from Components.config import config, configfile, getConfigListEntry
from Components.Console import Console
from Components.MenuList import MenuList
import xml.dom.minidom as xml
import os



g_timerinstance = None
g_session = None
g_location = ''



class cRemovePlugin(Screen):
	skin = """
	<screen position="c-150,c-100" size="400,120" title="">
		<widget source="statusbar" render="Label" position="c-300,e-100" zPosition="10" size="e-10,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<ePixmap pixmap="skin_default/buttons/red.png" position="c-150,e-45" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="c-0,e-45" size="140,40" alphatest="on" />
		<widget source="key_red" render="Label" position="c-150,e-45" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget source="key_green" render="Label" position="c-0,e-45" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
	</screen>"""

	def __init__(self, session):
		self.skin = cRemovePlugin.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"save": self.keyOk,
			"green": self.keyOk,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
		}, -2)
		self["key_red"] = StaticText("CANCEL")
		self["key_green"] = StaticText("OK")
		self["statusbar"] = StaticText("Press OK to remove factory test")

		self.onLayoutFinish.append(self.createTopMenu)

	def createTopMenu(self):
		self.setTitle(" ")

	def keyOk(self):
		os.system('rm -fR /etc/enigma2')
		os.system('rm -fR /etc/init.d/prepare-factorytest')
		os.system('rm -fR /etc/rc3.d/S90prepare-factorytest')
		os.system('rm -fR /usr/lib/enigma2/python/Plugins/Extensions/Factorytest')
		os._exit(0)

	def keyCancel(self):
		self.close()

class cFactoryTest_Tuner(Screen):
	skin = """
	<screen position="c-250,c-100" size="500,220" title="">
		<widget source="statusbar" render="Label" position="c-300,e-100" zPosition="10" size="e-10,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<ePixmap pixmap="skin_default/buttons/red.png" position="c-220,e-45" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="c-70,e-45" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="c+80,e-45" size="140,40" alphatest="on" />
		<widget source="key_red" render="Label" position="c-220,e-45" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget source="key_green" render="Label" position="c-70,e-45" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget source="key_blue" render="Label" position="c+80,e-45" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />

	</screen>"""

	def __init__(self, session):
		self.skin = cFactoryTest_Tuner.skin
		Screen.__init__(self, session)
		self["key_green"] = StaticText(" ")
		self["key_red"] = StaticText("CANCEL")
		self["key_blue"] = StaticText("SKIP")
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"save": self.keyOk,
			"green": self.keyOk,
			"red": self.keyCancel,
			"blue": self.keySkip,
		}, -2)

		self["statusbar"] = StaticText(" ")

		self.hasLock = False

		# reload just changed settings file
		configfile.load()
		InitNimManager(nimmanager)

		ret = self.openFrontend()
		self.tuner = Tuner(self.frontend)

		self.frontendStatus = { }
		self.lockState = TunerInfo(TunerInfo.LOCK_STATE, statusDict = self.frontendStatus)

		self.index = 0
		self.xmlFiles = []
		self.readMainXml()

		self.statusTimer = eTimer()
		self.statusTimer.callback.append(self.statusCallback)
		self.tuneSat()

	def statusCallback(self):
		self.frontend.getFrontendStatus(self.frontendStatus)
		self.lockState.update()
		print"lockState = %s" % self.lockState.getValue(TunerInfo.LOCK)
		if self.lockState.getValue(TunerInfo.LOCK) == 1:
			self["statusbar"].setText('Tuner has LOCK')
			self["key_green"].setText("OK")
			self.hasLock = True
		else:
			self["statusbar"].setText('Tuner not locked')
			self["key_green"].setText(" ")
			self.hasLock = False

	def readMainXml(self):
		xmlnode = []
		xmlnode = xml.parse('/etc/enigma2/factory_freq.xml')
		self.xmlFiles = []
		tmp = xmlnode.getElementsByTagName("transponder")
		for i in range(len(tmp)):
			location = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName("location")[0].childNodes))
			description = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName("description")[0].childNodes))
			frequency = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName("frequency")[0].childNodes))
			symbolrate = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName("symbolrate")[0].childNodes))
			polarization = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName("polarization")[0].childNodes))
			fec = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName("fec")[0].childNodes))
			inversion = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName("inversion")[0].childNodes))
			satpos = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName("satpos")[0].childNodes))
			system = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName("system")[0].childNodes))
			modulation = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName("modulation")[0].childNodes))
			rolloff = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName("rolloff")[0].childNodes))
			pilot = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName("pilot")[0].childNodes))
			self.xmlFiles.append((location, description, frequency, symbolrate, polarization, fec, inversion, satpos, system, modulation, rolloff, pilot))

	def stripLineEndings(self, buf):
		return buf.strip('\r\n').strip('\n').strip('\t')

	def getText(self, nodelist):
		rc = []
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				rc.append(node.data)
			return str(''.join(rc))

	def getCount(self, target):
		cnt = 0
		for x in self.xmlFiles:
			if x[0] == target:
				cnt += 1
		return cnt

	def openFrontend(self):
		nims = nimmanager.getNimListOfType("DVB-S")

		nimList = []
		for x in nims:
			print "NIMS: %s" % x
			nimList.append(x)

		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.raw_channel = res_mgr.allocateRawChannel(nimList[0])
			if self.raw_channel:
				self.frontend = self.raw_channel.getFrontend()
				if self.frontend:
					return True
				else:
					print "getFrontend failed"
			else:
				print "getRawChannel failed"
		else:
			print "getResourceManager instance failed"
		return False

	def clearGui(self):
		self["statusbar"].setText(" ")
		self["key_green"].setText(" ")

	def startTimer(self):
		self.statusTimer.start(2000)

	def keyOk(self):
		if self.hasLock is False:
			return
		self.tuneNext()

	def keyCancel(self):
		self.close()

	def keySkip(self):
		self.tuneNext()

	def tuneNext(self):
		self.hasLock = False
		self.clearGui()
		self.statusTimer.stop()
		self.tuneSat()

	def tuneSat(self):
		global g_location
		total = self.getCount(g_location)
		cnt = 0
		found = False
		for x in self.xmlFiles:
			if x[0] == g_location:
				if cnt == self.index:
					found = True
					break
				cnt += 1
		tmp = (int(x[2]), int(x[3]), int(x[4]), int(x[5]), int(x[6]), int(x[7]), int(x[8]), int(x[9]), int(x[10]), int(x[11]))
		if found:
			self.setTitle(x[1])
			self.tuner.tune(tmp)
			self.index += 1
			self.startTimer()
		else:
			self.close()

class cFactoryTest_FP(Screen):
	STATE_KEY_CHUP = 0
	STATE_KEY_CHDOWN = 1
	STATE_KEY_VOLUP = 2
	STATE_KEY_VOLDOWN = 3
	STATE_KEY_POWER = 4

	skin = """
	<screen position="c-150,c-100" size="400,120" title="">
		<widget source="statusbar" render="Label" position="c-300,e-100" zPosition="10" size="e-10,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		self.skin = cFactoryTest_FP.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["GlobalActions"],
		{
			"power_down" : self.keyPower,
			"power_up" : self.keyPower
		}, -2)

		self["statusbar"] = StaticText(" ")

		self.onLayoutFinish.append(self.createTopMenu)
		self.state = self.STATE_KEY_POWER

	def createTopMenu(self):
		self.setTitle("Frontpanel test ")
		self["statusbar"].setText("Press POWER on Frontpanel")

	def keyPower(self):
		if self.state != self.STATE_KEY_POWER:
			return
		self.close()

class cFactoryTest_VFD(Screen):
	skin = """
	<screen position="c-150,c-100" size="400,120" title="">
		<widget source="statusbar" render="Label" position="c-300,e-100" zPosition="10" size="e-10,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		self.skin = cFactoryTest_VFD.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"save": self.keyOk,
			"green": self.keyOk,
		}, -2)

		self["statusbar"] = StaticText(" ")
		self.setTitle("VFD test ")
		self.onLayoutFinish.append(self.keyOk)
		self.state = 0

	def keyOk(self):
		if self.state == 0:
			self.vfd_write("    ")
			self.state = 1
			self["statusbar"].setText("Press ok to switch off the VFD")
		elif self.state == 1:
			self.vfd_write("    ")
			self.state = 2
			self["statusbar"].setText("Press ok to switch on the VFD")
		elif self.state == 2:
			self.vfd_write("8888")
			self.state = 3
			self["statusbar"].setText("Press ok to continue")
		elif self.state == 3:
			self.vfd_write("    ")
			self.close()

	def vfd_write(self, text):
		f = open("/dev/dbox/oled0", "w")
		f.write(text)
		f.close()

class cFactoryTest_YUV(Screen):
	skin = """
	<screen position="c-150,c-100" size="400,120" title="">
		<widget source="statusbar" render="Label" position="c-300,e-100" zPosition="10" size="e-10,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		self.skin = cFactoryTest_YUV.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"save": self.keyOk,
			"green": self.keyOk,
		}, -2)

		self["statusbar"] = StaticText(" ")
		self.oldColorformat = "cvbs"

		f = open("/proc/stb/avs/0/colorformat", "r")
		self.oldColorformat = f.read()[:-1]
		f.close()

		self.onLayoutFinish.append(self.createTopMenu)
		self.state = 0

	def createTopMenu(self):
		self.setTitle("YUV test ")
		self["statusbar"].setText("Press ok to switch YUV")

	def keyOk(self):
		if self.state == 0:
			self.change_colorformat("yuv")
			self.state = 1
			self["statusbar"].setText("Press ok to continue")
		elif self.state == 1:
			self.change_colorformat(self.oldColorformat)
			self.close()

	def change_colorformat(self, colorformat):
		f = open("/proc/stb/avs/0/colorformat", "w")
		f.write(colorformat)
		f.close()

class cFactoryTest_USB(Screen):
	skin = """
	<screen position="c-170,c-100" size="440,120" title="">
		<widget source="statusbar" render="Label" position="c-300,e-100" zPosition="10" size="e-10,60" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		self.skin = cFactoryTest_USB.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"save": self.keyOk,
			"green": self.keyOk,
		}, -2)

		self["statusbar"] = StaticText(" ")

		self.remove_log()

		self.onLayoutFinish.append(self.createTopMenu)
		self.state = 0
		self.usblist = [ ]

	def createTopMenu(self):
		self.setTitle("USB test ")
		self["statusbar"].setText("Connect the USB stick to the BACK\nPress ok when ready")

	def keyOk(self):
		if self.state == 0:
			usbport = self.read_log()
			if usbport.find('usb 1-1:') > -1:
				self.state = 1
				self.umount_usb()
				self.remove_log()
				self["statusbar"].setText("Connect the USB stick to the FRONT port\nPress ok when ready")
			elif usbport.find('usb 2-1:') > -1:
				self.state = 1
				self.umount_usb()
				self.remove_log()
				self["statusbar"].setText("Connect the USB stick to the FRONT port\nPress ok when ready")
			else:
				return
		elif self.state == 1:
			usbport = self.read_log()
			if usbport.find('usb 1-2:') > -1:
				self.state = 2
				self.umount_usb()
				self.remove_log()
				self["statusbar"].setText("Remove the USB Stick\nPress ok to continue")
			elif usbport.find('usb 3-1:') > -1:
				self.state = 2
				self.umount_usb()
				self.remove_log()
				self["statusbar"].setText("Remove the USB Stick\nPress ok to continue")
			else:
				return
		elif self.state == 2:
			self.close()

	def read_log(self):
		tmp = 'no usb'
		if os.path.isfile('/var/log/messages'):
			f = open("/var/log/messages", "r")
			tmp = f.read()
			f.close()
		return tmp

	def remove_log(self):
		if os.path.isfile('/var/log/messages'):
			os.system('rm -f /var/log/messages')

	def umount_usb(self):
		os.system('umount /dev/sda1')

class cFactoryTest_Scart(Screen):
	skin = """
	<screen position="c-150,c-100" size="400,120" title="">
		<widget source="statusbar" render="Label" position="c-300,e-100" zPosition="10" size="e-10,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		self.skin = cFactoryTest_Scart.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"save": self.keyOk,
			"green": self.keyOk,
		}, -2)

		self["statusbar"] = StaticText(" ")

		open("/proc/stb/video/aspect", "w").write("4:3")
		self.onLayoutFinish.append(self.createTopMenu)
		self.state = 0

	def createTopMenu(self):
		self.setTitle("Scart test ")
		self["statusbar"].setText("Press ok to switch 16:9")

	def keyOk(self):
		if self.state == 0:
			open("/proc/stb/video/aspect", "w").write("16:9")
			self.state = 1
			self["statusbar"].setText("Press ok to switch 4:3")
		elif self.state == 1:
			open("/proc/stb/video/aspect", "w").write("4:3")
			self.state = 2
			self["statusbar"].setText("Press ok to continue")
		elif self.state == 2:
			open("/proc/stb/video/aspect", "w").write("16:9")
			self.close()

class cFactoryTest_Hdmi(Screen, ConfigListScreen):
	skin = """
	<screen position="c-300,c-250" size="600,500" title="">
		<widget name="config" position="25,25" size="550,400" />
		<widget source="statusbar" render="Label" position="c-300,e-45" zPosition="10" size="e-10,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		self.skin = cFactoryTest_Info.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions"],
		{
			"ok": self.keyOk,
			"save": self.keyOk,
			"up": self.keyUp,
			"down": self.keyDown,
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session)

		self["statusbar"] = StaticText(" ")

		self.data = '%s' % (readFile('/proc/stb/video/videomode_preferred'))
		tmp = self.data[2:-5].split(' ')
		for x in tmp:
			self.list.append(getConfigListEntry(('%s' % (x))))
		self["config"].list = self.list
		self["config"].l.setList(self.list)
		self.onLayoutFinish.append(self.createTopMenu)

	def createTopMenu(self):
		self.setTitle("Supported HDMI modes ")
		if len(self.data) > 0:
			self["statusbar"].setText("HDMI OK, press OK")
		else:
			self["statusbar"].setText("HDMI connection error")

	def keyOk(self):
		if len(self.data) > 0:
			self.close()

	def keyUp(self):
		return

	def keyDown(self):
		return

class cFactoryTest_Info(Screen, ConfigListScreen):
	skin = """
	<screen position="c-300,c-200" size="600,440" title="">
		<widget name="config" position="25,25" size="550,400" />
		<widget source="statusbar" render="Label" position="c-300,e-45" zPosition="10" size="e-10,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		self.skin = cFactoryTest_Info.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions"],
		{
			"ok": self.keyOk,
			"save": self.keyOk,
			"up": self.keyUp,
			"down": self.keyDown,
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session)

		self.Console = Console()
		self.Console.ePopen("ip -o addr show dev eth0", self.NetworkStatedataAvail, ['eth0', None])
		self["statusbar"] = StaticText(" ")

		self.onLayoutFinish.append(self.createTopMenu)

	def NetworkStatedataAvail(self, data, retval, extra_args):
		local_ip = ''
		sci0 = "/dev/sci0"
		sci1 = "/dev/sci1"
		for line in data.splitlines():
			tmp = line.split(": eth0")
			tmp2 = line.split("inet ")
			if len(tmp2) > 1:
				tmp3 = tmp2[1].split('/')
				local_ip = tmp3[0]
		tmp = readFile('/proc/stb/info/boxtype')
		self.list.append(getConfigListEntry(('boxtype %s' % (tmp[0]))))
		tmp = readFile('/proc/stb/info/board_revision')
		self.list.append(getConfigListEntry(('board revision %s' % (tmp[0]))))
		tmp = readFile('/sys/class/net/eth0/address')
		self.list.append(getConfigListEntry(('mac address %s' % (tmp[0]))))
		self.list.append(getConfigListEntry(('ip %s' % (local_ip))))
		tmp = readFile('/sys/class/net/eth0/speed')
		self.list.append(getConfigListEntry(('ethernet speed %s' % (tmp[0]))))
		self.list.append(getConfigListEntry("==================================="))
		if os.path.exists("/dev/sci0"):
			self.list.append(getConfigListEntry(('Cardreader found on %s' % (sci0))))
		if os.path.exists("/dev/sci1"):
			self.list.append(getConfigListEntry(('Cardreader found on %s' % (sci1))))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

		self["statusbar"].setText("Press OK to start tests")

	def createTopMenu(self):
		self.setTitle(" ")
		self["statusbar"].setText(" ")

	def keyOk(self):
		self.close()

	def keyUp(self):
		return

	def keyDown(self):
		return

class cFactoryTest_Start(Screen):
	skin = """
	<screen position="c-150,c-100" size="400,220" title="">
		<widget name="menu" position="10,10"   size="e-20,100" scrollbarMode="showOnDemand" />
		<widget source="statusbar" render="Label" position="c-300,e-40" zPosition="10" size="e-10,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		self.skin = cFactoryTest_Start.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyGo,
			"save": self.keyGo,
			"green": self.keyGo,
		}, -2)

		self["statusbar"] = StaticText(" ")
		self.mmenu= []
		self.mmenu.append(('China', 'china'))
		self.mmenu.append(('Korea', 'korea'))
		self.mmenu.append(('Europe', 'europe'))
		self["menu"] = MenuList(self.mmenu)

		self.onLayoutFinish.append(self.createTopMenu)

	def createTopMenu(self):
		self.setTitle(" ")
		self["statusbar"].setText("Choose location")

	def keyGo(self):
		selection = self["menu"].l.getCurrentSelection()
		global g_location
		if selection is not None:
			if selection[1] == 'china':
				g_location = 'china'
			if selection[1] == 'korea':
				g_location = 'korea'
			if selection[1] == 'europe':
				g_location = 'europe'
		configfile.load()
		InitNimManager(nimmanager)
		self.close()

class cFactoryTest_Setup(Screen):
	skin = """
	<screen position="c-150,c-100" size="400,220" title="">
		<widget name="menu" position="10,10"   size="e-20,100" scrollbarMode="showOnDemand" />
		<widget source="statusbar" render="Label" position="c-300,e-40" zPosition="10" size="e-10,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		self.skin = cFactoryTest_Setup.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyGo,
			"save": self.keyGo,
			"green": self.keyGo,
		}, -2)

		self["statusbar"] = StaticText(" ")
		self.mmenu= []
		self.mmenu.append(('direct', 'direct'))
		self.mmenu.append(('diseqc a/b', 'ab'))
		self.mmenu.append(('diseqc a/b/c/d', 'abcd'))
		self["menu"] = MenuList(self.mmenu)

		self.onLayoutFinish.append(self.createTopMenu)

	def createTopMenu(self):
		self.setTitle(" ")
		global g_location
		if g_location == 'china':
			self["statusbar"].setText("Chinasat 115.5E is connected to")
		if g_location == 'korea':
			self["statusbar"].setText("Asiasat 105.6E is connected to")
		if g_location == 'europe':
			self["statusbar"].setText("Astra 19.2E is connected to")

	def keyGo(self):
		global g_location
		selection = self["menu"].l.getCurrentSelection()
		if selection is not None:
			if selection[1] == 'direct':
				if g_location == 'china':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=single\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1155\n')
				if g_location == 'korea':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=single\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1056\n')
				if g_location == 'europe':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=single\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=192\n')
				self.close('done')
			if selection[1] == 'ab':
					self.close('ab')
			if selection[1] == 'abcd':
					self.close('abcd')

class cFactoryTest_DiseqcAB(Screen):
	skin = """
	<screen position="c-150,c-100" size="400,220" title="">
		<widget name="menu" position="10,10"   size="e-20,100" scrollbarMode="showOnDemand" />
		<widget source="statusbar" render="Label" position="c-300,e-40" zPosition="10" size="e-10,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		self.skin = cFactoryTest_DiseqcAB.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyGo,
			"save": self.keyGo,
			"green": self.keyGo,
		}, -2)

		self["statusbar"] = StaticText(" ")
		self.mmenu= []
		self.mmenu.append(('port A', 'a'))
		self.mmenu.append(('port B', 'b'))
		self["menu"] = MenuList(self.mmenu)

		self.onLayoutFinish.append(self.createTopMenu)

	def createTopMenu(self):
		self.setTitle(" ")
		global g_location
		if g_location == 'china':
			self["statusbar"].setText("Chinasat 115.5E is connected to")
		if g_location == 'korea':
			self["statusbar"].setText("Asiasat 105.6E is connected to")
		if g_location == 'europe':
			self["statusbar"].setText("Astra 19.2E is connected to")

	def keyGo(self):
		global g_location
		selection = self["menu"].l.getCurrentSelection()
		if selection is not None:
			if selection[1] == 'a':
				if g_location == 'china':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1155\nconfig.Nims.0.diseqcB=1056\n')
				if g_location == 'korea':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1056\nconfig.Nims.0.diseqcB=1155\n')
				if g_location == 'europe':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=192\nconfig.Nims.0.diseqcB=235\n')
			if selection[1] == 'b':
				if g_location == 'china':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1056\nconfig.Nims.0.diseqcB=1155n')
				if g_location == 'korea':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1155\nconfig.Nims.0.diseqcB=1056\n')
				if g_location == 'europe':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=235\nconfig.Nims.0.diseqcB=192\n')
		self.close('done')

class cFactoryTest_DiseqcABCD(Screen):
	skin = """
	<screen position="c-150,c-100" size="400,220" title="">
		<widget name="menu" position="10,10"   size="e-20,100" scrollbarMode="showOnDemand" />
		<widget source="statusbar" render="Label" position="c-300,e-40" zPosition="10" size="e-10,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		self.skin = cFactoryTest_DiseqcABCD.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyGo,
			"save": self.keyGo,
			"green": self.keyGo,
		}, -2)

		self["statusbar"] = StaticText(" ")
		self.mmenu= []
		self.mmenu.append(('port A', 'a'))
		self.mmenu.append(('port B', 'b'))
		self.mmenu.append(('port C', 'c'))
		self.mmenu.append(('port D', 'd'))
		self["menu"] = MenuList(self.mmenu)

		self.onLayoutFinish.append(self.createTopMenu)

	def createTopMenu(self):
		self.setTitle(" ")
		global g_location
		if g_location == 'china':
			self["statusbar"].setText("ChinaSat 115.5E is connected to")
		if g_location == 'korea':
			self["statusbar"].setText("Asiasat 105.6E is connected to")
		if g_location == 'europe':
			self["statusbar"].setText("Astra 19.2E is connected to")

	def keyGo(self):
		global g_location
		selection = self["menu"].l.getCurrentSelection()
		if selection is not None:
			if selection[1] == 'a':
				if g_location == 'china':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=diseqc_a_b_c_d\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1155\nconfig.Nims.0.diseqcB=1056\n')

				if g_location == 'korea':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=diseqc_a_b_c_d\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1056\nconfig.Nims.0.diseqcB=1155\n')

				if g_location == 'europe':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=diseqc_a_b_c_d\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=192\nconfig.Nims.0.diseqcB=235\n')

			if selection[1] == 'b':
				if g_location == 'china':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=diseqc_a_b_c_d\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1056\nconfig.Nims.0.diseqcB=1155\n')

				if g_location == 'korea':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=diseqc_a_b_c_d\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1155\nconfig.Nims.0.diseqcB=1056\n')

				if g_location == 'europe':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=diseqc_a_b_c_d\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=235\nconfig.Nims.0.diseqcB=192\n')
					
			if selection[1] == 'c':
				if g_location == 'china':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=diseqc_a_b_c_d\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1056\nconfig.Nims.0.diseqcC=1155\n')

				if g_location == 'korea':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=diseqc_a_b_c_d\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1155\nconfig.Nims.0.diseqcC=1056\n')

				if g_location == 'europe':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=diseqc_a_b_c_d\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=235\nconfig.Nims.0.diseqcC=192\n')
			if selection[1] == 'd':
				if g_location == 'china':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=diseqc_a_b_c_d\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1056\nconfig.Nims.0.diseqcD=1155\n')

				if g_location == 'korea':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=diseqc_a_b_c_d\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=1155\nconfig.Nims.0.diseqcD=1056\n')

				if g_location == 'europe':
					writeFile('/etc/enigma2/settings', 'config.Nims.0.diseqcMode=diseqc_a_b_c_d\nconfig.Nims.0.configMode=simple\nconfig.Nims.0.diseqcA=235\nconfig.Nims.0.diseqcD=192\n')
		self.close('done')

def writeFile(name, data):
	fp = open(name, 'a')
	fp.write(data)
	fp.close()

def readFile(name):
	try:
		lines = open(name).readlines()
		return lines
	except:
		return ''
		pass

def step0():
	global g_session
	g_session.openWithCallback(step1, cFactoryTest_Start)

def step1():
	global g_session
	g_session.openWithCallback(step2, cFactoryTest_Setup)

def step2(retval):
	global g_session
	if retval == 'done':
		step10()
	elif retval == 'ab':
		g_session.openWithCallback(step2, cFactoryTest_DiseqcAB)
	elif retval == 'abcd':
		g_session.openWithCallback(step2, cFactoryTest_DiseqcABCD)

def step10():
	global g_session
	g_session.openWithCallback(step20, cFactoryTest_Info)

def step20():
	global g_session
	g_session.openWithCallback(step50, cFactoryTest_FP)

def step30():
	#skip VFD test because Ixuss One doesnt have a VFD
	global g_session
	g_session.openWithCallback(step40, cFactoryTest_VFD)

def step40():
	#skip YUV test because Ixuss One doesnt have a YUV
	global g_session
	g_session.openWithCallback(step50, cFactoryTest_YUV)

def step50():
	global g_session
	g_session.openWithCallback(step70, cFactoryTest_USB)

def step60():
	#skip SCART test because Ixuss One doesnt have a SCART
	global g_session
	g_session.openWithCallback(step70, cFactoryTest_Scart)

def step70():
	global g_session
	g_session.openWithCallback(step80, cFactoryTest_Hdmi)

def step80():
	global g_session
	g_session.openWithCallback(step90, cFactoryTest_Tuner)

def step90():
	print 'done?'

def timerCallback():
	global g_timerinstance
	g_timerinstance.stop()
	step0()

def autostart(session, **kwargs):
	global g_session
	g_session = session
	global g_timerinstance
	g_timerinstance = eTimer()
	g_timerinstance.callback.append(timerCallback)
	g_timerinstance.start(5 * 1000)

def main(session, **kwargs):
	session.open(cRemovePlugin)

def mainInMenu(menuid, **kwargs):
	print menuid
	if menuid == "mainmenu":
		return [(("Remove factory Test"), main, "removefactorytest", 99)]
	else:
		return []

def Plugins(**kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart), \
		PluginDescriptor(name = "Remove factory Test", description = "Remove factory Test", where = PluginDescriptor.WHERE_MENU, fnc = mainInMenu)]
