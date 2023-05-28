import microcontroller
import config

def reset_reason():
    # print version and the last reset reason
    reset_reason = 0
    if microcontroller.cpu.reset_reason == microcontroller.ResetReason.POWER_ON:
        message = "VERSION: {}, the last reset was due to HARDWARE".format(config.version)
        reset_reason = 1
    elif microcontroller.cpu.reset_reason == microcontroller.ResetReason.SOFTWARE:
        message = "VERSION: {}, the last reset was due to SOFTWARE".format(config.version)
        reset_reason = 2
    else :
        message = "VERSION: {}, unknown cpu reset code: {}".format(config.version, microcontroller.cpu.reset_reason)

    return reset_reason, message
