include $(BUILD_DIR)/src/Makefile

rama-probe:
	$(CXX) $(DEFS) $(DEFAULT_INCLUDES) $(INCLUDES) $(AM_CPPFLAGS) $(CPPFLAGS) $(AM_CXXFLAGS) $(CXXFLAGS) -fno-access-control -dynamiclib -undefined dynamic_lookup $(RELEASE_DIR)/rama-probe.cc -o $(PROBE_OUTPUT)
