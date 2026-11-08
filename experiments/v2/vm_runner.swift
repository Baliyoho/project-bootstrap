import Foundation
import Virtualization

if CommandLine.arguments.count != 6 {
    fputs("usage: vm_runner KERNEL INITRAMFS SHARE_DIR STOP_AFTER_SECONDS PROBE_ID\n", stderr)
    exit(2)
}
let kernel = URL(fileURLWithPath: CommandLine.arguments[1])
let ramdisk = URL(fileURLWithPath: CommandLine.arguments[2])
let shareDir = URL(fileURLWithPath: CommandLine.arguments[3])
let stopAfter = Double(CommandLine.arguments[4]) ?? 0
let boot = VZLinuxBootLoader(kernelURL: kernel)
boot.initialRamdiskURL = ramdisk
boot.commandLine = "console=hvc0 rdinit=/init devtmpfs.mount=1 probe_id=\(CommandLine.arguments[5])"
let config = VZVirtualMachineConfiguration()
config.cpuCount = 2
config.memorySize = 512 * 1024 * 1024
config.bootLoader = boot
let serial = VZVirtioConsoleDeviceSerialPortConfiguration()
serial.attachment = VZFileHandleSerialPortAttachment(
    fileHandleForReading: FileHandle.standardInput,
    fileHandleForWriting: FileHandle.standardOutput
)
config.serialPorts = [serial]
config.networkDevices = []
let fs = VZVirtioFileSystemDeviceConfiguration(tag: "probe")
fs.share = VZSingleDirectoryShare(directory: VZSharedDirectory(url: shareDir, readOnly: false))
config.directorySharingDevices = [fs]
do {
    try config.validate()
    fputs("HOST_CONFIG_VALID\n", stderr)
} catch {
    fputs("HOST_CONFIG_ERROR \(error)\n", stderr)
    exit(3)
}
let vm = VZVirtualMachine(configuration: config)
vm.start { result in
    if case .failure(let error) = result {
        fputs("HOST_START_ERROR \(error)\n", stderr)
        exit(4)
    }
    fputs("HOST_STARTED\n", stderr)
    if stopAfter > 0 {
        DispatchQueue.main.asyncAfter(deadline: .now() + stopAfter) {
            guard vm.canStop else {
                fputs("HOST_CANNOT_STOP state=\(vm.state.rawValue)\n", stderr)
                exit(5)
            }
            vm.stop { error in
                if let error = error {
                    fputs("HOST_STOP_ERROR \(error)\n", stderr)
                    exit(6)
                }
                fputs("HOST_STOPPED state=\(vm.state.rawValue)\n", stderr)
                exit(0)
            }
        }
    }
}
RunLoop.current.run()
