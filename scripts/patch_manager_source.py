#!/usr/bin/env python3
from pathlib import Path

p = Path('Manager.mm')
s = p.read_text()

needle = 'static NSString * const kLangKey = @"multiface.language";'
if 'multiface.safe.pending' not in s:
    s = s.replace(needle, needle + '\nstatic NSString * const kSafePendingKey = @"multiface.safe.pending";', 1)

old_switch = '''- (void)switchChanged:(UISwitch *)sender {\n    NSString *key = sender.accessibilityIdentifier;\n    if (!key.length) return;\n    MTSetPref(key, sender.isOn);\n}\n'''
new_switch = '''- (void)switchChanged:(UISwitch *)sender {\n    // Do not persist until Done is tapped.\n    (void)sender;\n}\n'''
if old_switch in s:
    s = s.replace(old_switch, new_switch, 1)
elif 'Do not persist until Done is tapped' not in s:
    raise SystemExit('switchChanged block not found')

old_tail = '''static void MTApplySelectedTweaks(void) {\n    BOOL iqFace = MTPref(kMxKey);\n    BOOL glow = MTPref(kIQKey);\n    BOOL wolf = MTPref(kLeadKey);\n\n    if (!(iqFace || glow || wolf)) return;\n    if (!MTEnsureSubstrateRuntime()) return;\n\n    if (iqFace) MTRunInitializers("iQFace.dylib");\n    if (glow)   MTRunInitializers("Glow.dylib");\n    if (wolf)   MTRunInitializers("Wolf.dylib");\n}\n\n__attribute__((constructor)) static void MultiFaceInit(void) {\n    @autoreleasepool {\n        MTApplySelectedTweaks();\n        dispatch_async(dispatch_get_main_queue(), ^{\n            [[NSNotificationCenter defaultCenter] addObserverForName:UIApplicationDidBecomeActiveNotification object:nil queue:NSOperationQueue.mainQueue usingBlock:^(__unused NSNotification *note) {\n                MTAttachGesture();\n                dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{ MTAttachGesture(); });\n            }];\n            MTAttachGesture();\n            dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{ MTAttachGesture(); });\n        });\n    }\n}\n'''
new_tail = '''static BOOL MTHadInterruptedTweakBoot(void) {\n    return [[NSUserDefaults standardUserDefaults] boolForKey:kSafePendingKey];\n}\n\nstatic void MTSetSafePending(BOOL value) {\n    NSUserDefaults *d = [NSUserDefaults standardUserDefaults];\n    [d setBool:value forKey:kSafePendingKey];\n    [d synchronize];\n}\n\nstatic void MTDisableAllTweaks(void) {\n    MTSetPref(kMxKey, NO);\n    MTSetPref(kIQKey, NO);\n    MTSetPref(kLeadKey, NO);\n}\n\nstatic BOOL MTHasSelectedTweaks(void) {\n    return MTPref(kMxKey) || MTPref(kIQKey) || MTPref(kLeadKey);\n}\n\nstatic void MTApplySelectedTweaks(void) {\n    BOOL iqFace = MTPref(kMxKey);\n    BOOL glow = MTPref(kIQKey);\n    BOOL wolf = MTPref(kLeadKey);\n\n    if (!(iqFace || glow || wolf)) return;\n    if (!MTEnsureSubstrateRuntime()) return;\n\n    MTSetSafePending(YES);\n    if (iqFace) MTRunInitializers("iQFace.dylib");\n    if (glow)   MTRunInitializers("Glow.dylib");\n    if (wolf)   MTRunInitializers("Wolf.dylib");\n    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(6.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{\n        MTSetSafePending(NO);\n    });\n}\n\n__attribute__((constructor)) static void MultiFaceInit(void) {\n    @autoreleasepool {\n        if (MTHadInterruptedTweakBoot()) {\n            MTDisableAllTweaks();\n            MTSetSafePending(NO);\n            NSLog(@"[MultiFace] Safe Mode: previous tweak boot failed; all tweaks disabled");\n        }\n\n        dispatch_async(dispatch_get_main_queue(), ^{\n            __block BOOL didApply = NO;\n            [[NSNotificationCenter defaultCenter] addObserverForName:UIApplicationDidBecomeActiveNotification object:nil queue:NSOperationQueue.mainQueue usingBlock:^(__unused NSNotification *note) {\n                MTAttachGesture();\n                dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.8 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{\n                    MTAttachGesture();\n                    if (!didApply && MTHasSelectedTweaks()) {\n                        didApply = YES;\n                        MTApplySelectedTweaks();\n                    }\n                });\n            }];\n            MTAttachGesture();\n            dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{ MTAttachGesture(); });\n        });\n    }\n}\n'''
if old_tail in s:
    s = s.replace(old_tail, new_tail, 1)
elif 'MTHadInterruptedTweakBoot' not in s:
    raise SystemExit('apply/constructor block not found')

p.write_text(s)
print('Patched Manager.mm for delayed apply + safe mode + Done-only persistence')
