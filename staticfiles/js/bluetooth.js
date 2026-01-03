/**
 * Web Bluetooth API implementation for Digital E-Paper Business Card
 * Handles connection to ESP32-C3 device and data synchronization
 */

class BluetoothSync {
    constructor() {
        this.serviceUUID = '4fafc201-1fb5-459e-8fcc-c5c9c331914b';
        this.characteristicUUID = 'beb5483e-36e1-4688-b7f5-ea07361b26a8';
        this.device = null;
        this.server = null;
        this.characteristic = null;
    }

    /**
     * Request Bluetooth device and establish connection
     */
    async connectToDevice() {
        if (!this.isWebBluetoothSupported()) {
            throw new Error('Web Bluetooth API not supported on this browser');
        }

        try {
            console.log('Requesting Bluetooth device...');
            
            this.device = await navigator.bluetooth.requestDevice({
                filters: [
                    { namePrefix: 'Digital_Badge_V1' },
                    { services: [this.serviceUUID] }
                ],
                optionalServices: [this.serviceUUID]
            });

            console.log('Device selected:', this.device.name);

            // Add event listener for device disconnection
            this.device.addEventListener('gattserverdisconnected', this.onDisconnected.bind(this));

            // Connect to GATT server
            console.log('Connecting to GATT server...');
            this.server = await this.device.gatt.connect();
            console.log('GATT server connected');

            // Get the primary service
            console.log('Getting primary service...');
            const primaryService = await this.server.getPrimaryService(this.serviceUUID);
            console.log('Primary service found');

            // Get the characteristic
            console.log('Getting characteristic...');
            this.characteristic = await primaryService.getCharacteristic(this.characteristicUUID);
            console.log('Characteristic found');

            console.log('Connected to device successfully!');
            return true;
        } catch (error) {
            console.error('Error connecting to device:', error);
            // Provide more specific error messages
            if (error.name === 'NotAllowedError') {
                throw new Error('Bluetooth connection not allowed. Please ensure you are using HTTPS and have granted permission.');
            } else if (error.name === 'NotFoundError') {
                throw new Error('No compatible device found. Please make sure your badge is powered on and in range.');
            } else if (error.name === 'NotSupportedError') {
                throw new Error('GATT operation not supported. The device may not be properly configured or compatible.');
            } else {
                throw error;
            }
        }
    }

    /**
     * Send profile data to the connected device
     */
  async sendProfileData(fullName, jobTitle, profileUrl) {
    if (!this.characteristic) throw new Error('No device connected.');

    try {
        const dataString = `${fullName}|${jobTitle}|${profileUrl}`;
        const encoder = new TextEncoder();
        const data = encoder.encode(dataString);

        // GATT hatasını önlemek için güvenli yazma metodu
        if (this.characteristic.writeValueWithResponse) {
            await this.characteristic.writeValueWithResponse(data);
        } else {
            await this.characteristic.writeValue(data);
        }
        
        console.log('Data sent successfully!');
        return true;
    } catch (error) {
        // Hata durumunda cihazı unut ve tekrar dene uyarısı ver
        if (error.name === 'NotSupportedError') {
             throw new Error('Cihazla güvenli bağ kurulamadı. Lütfen telefon/bilgisayar Bluetooth ayarlarından cihazı "Unut" diyip tekrar deneyin.');
        }
        throw error;
    }
}

    /**
     * Disconnect from the device
     */
    async disconnect() {
        if (this.device && this.device.gatt.connected) {
            this.device.gatt.disconnect();
            console.log('Device disconnected');
        }
    }

    /**
     * Check if Web Bluetooth API is supported
     */
    isWebBluetoothSupported() {
        return 'bluetooth' in navigator;
    }

    /**
     * Handle device disconnection
     */
    onDisconnected(event) {
        console.log('Device disconnected:', event.target.name);
        this.device = null;
        this.server = null;
        this.characteristic = null;
    }
}

// Initialize Bluetooth Sync when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const bluetoothSync = new BluetoothSync();
    
    // If there's a sync button on the page, attach event listener
    const syncButton = document.getElementById('connectButton');
    if (syncButton) {
        // Get profile data from data attributes on the button or page
        const fullName = syncButton.dataset.fullName || document.querySelector('[data-full-name]')?.dataset.fullName;
        const jobTitle = syncButton.dataset.jobTitle || document.querySelector('[data-job-title]')?.dataset.jobTitle;
        const profileUrl = syncButton.dataset.profileUrl || document.querySelector('[data-profile-url]')?.dataset.profileUrl;
        
        syncButton.addEventListener('click', async function() {
            const statusDiv = document.getElementById('status');
            
            try {
                statusDiv.innerHTML = '<span class="text-blue-600">Connecting to device...</span>';
                
                // Attempt to connect
                await bluetoothSync.connectToDevice();
                statusDiv.innerHTML = '<span class="text-blue-600">Connected! Sending data...</span>';
                
                // Use profile data from data attributes or fallback to template values
                const fullName = syncButton.dataset.fullName;
                const jobTitle = syncButton.dataset.jobTitle;
                const profileUrl = syncButton.dataset.profileUrl;
                
                // Validate that we have the required data
                if (!fullName || !jobTitle || !profileUrl) {
                    throw new Error('Profile data is missing. Please ensure you are on the dashboard page.');
                }
                
                // Send profile data
                await bluetoothSync.sendProfileData(fullName, jobTitle, profileUrl);
                
                statusDiv.innerHTML = '<span class="text-green-600">Successfully synced to badge!</span>';
            } catch (error) {
                console.error('Sync error:', error);
                statusDiv.innerHTML = `<span class="text-red-600">Error: ${error.message}</span>`;
            }
        });
    }
});