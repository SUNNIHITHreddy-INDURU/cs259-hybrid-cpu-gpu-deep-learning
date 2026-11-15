// timing.cpp - platform metadata (CPU model, thread count, compiler) for result files.
#include "timing.hpp"

#include <fstream>
#include <thread>

#if defined(__APPLE__)
#include <sys/sysctl.h>
#endif

namespace nn {

PlatformInfo query_platform() {
  PlatformInfo p;
  p.logical_threads = static_cast<int>(std::thread::hardware_concurrency());
#if defined(__APPLE__)
  char buf[256];
  size_t len = sizeof(buf);
  if (sysctlbyname("machdep.cpu.brand_string", buf, &len, nullptr, 0) == 0) p.cpu_model = buf;
#else
  std::ifstream cpuinfo("/proc/cpuinfo");
  std::string line;
  while (std::getline(cpuinfo, line)) {
    if (line.rfind("model name", 0) == 0) {
      const auto pos = line.find(':');
      if (pos != std::string::npos) p.cpu_model = line.substr(pos + 2);
      break;
    }
  }
#endif
  if (p.cpu_model.empty()) p.cpu_model = "unknown";
  for (char& c : p.cpu_model)
    if (c == ',') c = ' ';  // keep CSV rows well-formed
  p.compiler = __VERSION__;
  for (char& c : p.compiler)
    if (c == ',' || c == '\n') c = ' ';
  return p;
}

}  // namespace nn
