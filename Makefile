ARCHS = arm64
TARGET = iphone:clang:latest:15.0
INSTALL_TARGET_PROCESSES = Facebook

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = MultiFace
MultiFace_FILES = Manager.mm
MultiFace_FRAMEWORKS = UIKit Foundation
MultiFace_CFLAGS = -fobjc-arc -Wall -Wextra
MultiFace_CCFLAGS = -std=c++17

include $(THEOS_MAKE_PATH)/tweak.mk
