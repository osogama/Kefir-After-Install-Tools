#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Edilson Alzemand
 
import pynotify
pynotify.init("Aplicativo")
notify = pynotify.Notification("Kefir After Install ", "Installation Complete", "/opt/kefir-after-install/lib/icons/kefir_icon.png")
notify.show()



