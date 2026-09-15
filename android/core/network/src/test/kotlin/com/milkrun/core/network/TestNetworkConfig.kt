package com.milkrun.core.network

import com.milkrun.core.network.config.NetworkConfig

class TestNetworkConfig(override val baseUrl: String = "http://localhost", override val isDebug: Boolean = false) :
    NetworkConfig
