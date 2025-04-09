
// Water Heater Data Backup Loader
// This script ensures all 8 water heaters appear in the UI by loading from a backup file
// when API calls fail or don't return all expected water heaters

document.addEventListener('DOMContentLoaded', () => {
  // Wait for the WaterHeaterList class to load
  setTimeout(() => {
    console.log('Water Heater Patch: Initializing backup data support');

    // Keep track of the original loadHeaters method
    if (window.WaterHeaterList && WaterHeaterList.prototype) {
      const originalLoadHeaters = WaterHeaterList.prototype.loadHeaters;

      // Override the loadHeaters method to add backup data support
      WaterHeaterList.prototype.loadHeaters = async function() {
        try {
          // First try the original method
          await originalLoadHeaters.call(this);

          // If we have fewer than 8 water heaters, load from backup
          if (!this.heaters || this.heaters.length < 8) {
            console.log(`Water Heater Patch: Only found ${this.heaters ? this.heaters.length : 0} water heaters, loading from backup`);
            await this.loadBackupData();
          } else {
            console.log(`Water Heater Patch: Found ${this.heaters.length} water heaters, no need for backup`);
          }
        } catch (error) {
          console.error('Water Heater Patch: Error in loadHeaters:', error);
          // Load from backup if any error occurs
          await this.loadBackupData();
        }
      };

      // Add method to load from backup data
      WaterHeaterList.prototype.loadBackupData = async function() {
        try {
          const backupUrl = '/static/data/water_heaters_backup.json';
          console.log('Water Heater Patch: Loading from backup:', backupUrl);

          const response = await fetch(backupUrl);
          if (response.ok) {
            const backupData = await response.json();

            if (Array.isArray(backupData) && backupData.length > 0) {
              console.log(`Water Heater Patch: Loaded ${backupData.length} water heaters from backup`);

              // If we already have some heaters, merge the backup data
              if (this.heaters && this.heaters.length > 0) {
                const existingIds = new Set(this.heaters.map(h => h.id));

                // Add only new water heaters from backup
                for (const heater of backupData) {
                  if (!existingIds.has(heater.id)) {
                    this.heaters.push(heater);
                    existingIds.add(heater.id);
                  }
                }

                console.log(`Water Heater Patch: Total water heaters after merge: ${this.heaters.length}`);
              } else {
                // If we have no heaters, use the backup data
                this.heaters = backupData;
              }

              // Render the updated list
              this.render();
              return true;
            }
          } else {
            console.warn(`Water Heater Patch: Failed to load backup data: ${response.status} ${response.statusText}`);
          }
        } catch (error) {
          console.error('Water Heater Patch: Error loading backup data:', error);
        }

        return false;
      };

      // Also patch the WaterHeaterDetail class to load history data from backup
      if (window.WaterHeaterDetail && WaterHeaterDetail.prototype) {
        const originalDetailLoadHeater = WaterHeaterDetail.prototype.loadHeater;

        WaterHeaterDetail.prototype.loadHeater = async function() {
          try {
            // First try the original method
            await originalDetailLoadHeater.call(this);

            // If no readings data, try to get it from backup
            if (!this.heater.readings || this.heater.readings.length === 0) {
              console.log('Water Heater Patch: No readings data, loading from backup');
              await this.loadBackupDataForDetail();
            }
          } catch (error) {
            console.error('Water Heater Patch: Error in loadHeater:', error);
            // Load from backup if any error occurs
            await this.loadBackupDataForDetail();
          }
        };

        // Add method to load detail data from backup
        WaterHeaterDetail.prototype.loadBackupDataForDetail = async function() {
          try {
            const backupUrl = '/static/data/water_heaters_backup.json';
            console.log('Water Heater Patch: Loading detail from backup:', backupUrl);

            const response = await fetch(backupUrl);
            if (response.ok) {
              const backupData = await response.json();

              // Find this water heater in the backup data
              const backupHeater = backupData.find(h => h.id === this.heaterId);
              if (backupHeater) {
                console.log(`Water Heater Patch: Found water heater ${this.heaterId} in backup`);

                // If we already have a heater object, merge the backup data
                if (this.heater) {
                  // Copy readings and any missing properties
                  this.heater.readings = backupHeater.readings || [];

                  for (const [key, value] of Object.entries(backupHeater)) {
                    if (this.heater[key] === undefined || this.heater[key] === null) {
                      this.heater[key] = value;
                    }
                  }
                } else {
                  // If we have no heater object, use the backup data
                  this.heater = backupHeater;
                }

                // Re-initialize the chart with the new data
                this.initCharts();
                return true;
              } else {
                console.warn(`Water Heater Patch: Water heater ${this.heaterId} not found in backup`);
              }
            } else {
              console.warn(`Water Heater Patch: Failed to load backup data: ${response.status} ${response.statusText}`);
            }
          } catch (error) {
            console.error('Water Heater Patch: Error loading backup data:', error);
          }

          return false;
        };
      }

      console.log('Water Heater Patch: Initialization complete');
    } else {
      console.warn('Water Heater Patch: WaterHeaterList class not found, patch not applied');
    }
  }, 500); // Wait 500ms to ensure classes are loaded
});
