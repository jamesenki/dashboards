// Water Heater Data Backup Loader - FIXED VERSION
// This script ensures water heaters appear correctly in the UI by loading from a backup file
// when API calls fail or don't return all expected water heaters
// Also prevents duplicate cards from appearing in the UI

document.addEventListener('DOMContentLoaded', () => {
  // Wait for the WaterHeaterList class to load
  setTimeout(() => {
    console.log('Water Heater Patch (Fixed): Initializing backup data support');

    // Keep track of the original loadHeaters method
    if (window.WaterHeaterList && WaterHeaterList.prototype) {
      const originalLoadHeaters = WaterHeaterList.prototype.loadHeaters;

      // Override the loadHeaters method to add backup data support
      WaterHeaterList.prototype.loadHeaters = async function() {
        try {
          // First try the original method
          await originalLoadHeaters.call(this);

          // First deduplicate any existing heaters
          if (this.heaters && this.heaters.length > 0) {
            const uniqueIds = new Set();
            const uniqueHeaters = [];

            for (const heater of this.heaters) {
              if (heater && heater.id && !uniqueIds.has(heater.id)) {
                uniqueIds.add(heater.id);
                uniqueHeaters.push(heater);
              }
            }

            if (uniqueHeaters.length < this.heaters.length) {
              console.log(`Water Heater Patch (Fixed): Removed ${this.heaters.length - uniqueHeaters.length} duplicate heaters`);
              this.heaters = uniqueHeaters;
            }
          }

          // Only load from backup if necessary
          if (!this.heaters || this.heaters.length < 2) {
            console.log(`Water Heater Patch (Fixed): Only found ${this.heaters ? this.heaters.length : 0} water heaters, loading from backup`);
            await this.loadBackupData();
          } else {
            console.log(`Water Heater Patch (Fixed): Found ${this.heaters.length} unique water heaters, no need for backup`);
            this.render(); // Ensure UI is up-to-date with deduplicated data
          }
        } catch (error) {
          console.error('Water Heater Patch (Fixed): Error in loadHeaters:', error);
          // Load from backup if any error occurs
          await this.loadBackupData();
        }
      };

      // Add method to load from backup data
      WaterHeaterList.prototype.loadBackupData = async function() {
        try {
          const backupUrl = '/static/data/water_heaters_backup.json';
          console.log('Water Heater Patch (Fixed): Loading from backup:', backupUrl);

          const response = await fetch(backupUrl);
          if (response.ok) {
            const backupData = await response.json();

            if (Array.isArray(backupData) && backupData.length > 0) {
              console.log(`Water Heater Patch (Fixed): Loaded ${backupData.length} water heaters from backup`);

              // Start fresh with a deduplicated list
              let finalHeaters = [];
              const allIds = new Set();

              // First, take existing non-duplicate heaters
              if (this.heaters && this.heaters.length > 0) {
                for (const heater of this.heaters) {
                  if (heater && heater.id && !allIds.has(heater.id)) {
                    finalHeaters.push(heater);
                    allIds.add(heater.id);
                  }
                }
              }

              // Then add non-duplicate backup heaters
              for (const heater of backupData) {
                if (heater && heater.id && !allIds.has(heater.id)) {
                  finalHeaters.push(heater);
                  allIds.add(heater.id);
                }
              }

              // Replace the heaters array with our clean, deduplicated version
              this.heaters = finalHeaters;
              console.log(`Water Heater Patch (Fixed): Total water heaters after deduplication: ${this.heaters.length}`);

              // Render the updated list
              this.render();
              return true;
            }
          } else {
            console.warn(`Water Heater Patch (Fixed): Failed to load backup data: ${response.status} ${response.statusText}`);
          }
        } catch (error) {
          console.error('Water Heater Patch (Fixed): Error loading backup data:', error);
        }

        return false;
      };

      // Add an additional cleanup method to remove duplicates from the heater list
      WaterHeaterList.prototype.removeDuplicateHeaters = function() {
        if (!this.heaters || !Array.isArray(this.heaters)) {
          return;
        }

        const uniqueIds = new Set();
        const uniqueHeaters = [];

        for (const heater of this.heaters) {
          if (heater && heater.id && !uniqueIds.has(heater.id)) {
            uniqueIds.add(heater.id);
            uniqueHeaters.push(heater);
          }
        }

        if (uniqueHeaters.length < this.heaters.length) {
          console.log(`Water Heater Patch (Fixed): Cleaned up ${this.heaters.length - uniqueHeaters.length} duplicate heaters`);
          this.heaters = uniqueHeaters;
          this.render();
        }
      };

      // Override the render method to ensure no duplicates before rendering
      const originalRender = WaterHeaterList.prototype.render;
      WaterHeaterList.prototype.render = function() {
        this.removeDuplicateHeaters();
        console.log(`Water Heater Patch (Fixed): Rendering ${this.heaters?.length || 0} unique water heaters`);
        return originalRender.call(this);
      };

      // Also patch the WaterHeaterDetail class to load history data from backup
      if (window.WaterHeaterDetail && WaterHeaterDetail.prototype) {
        const originalDetailLoadHeater = WaterHeaterDetail.prototype.loadHeater;

        WaterHeaterDetail.prototype.loadHeater = async function() {
          try {
            // First try the original method
            await originalDetailLoadHeater.call(this);

            // If no readings data, try to get it from backup
            if (!this.heater || !this.heater.readings || this.heater.readings.length === 0) {
              console.log('Water Heater Patch (Fixed): No readings data, loading from backup');
              await this.loadBackupDataForDetail();
            }
          } catch (error) {
            console.error('Water Heater Patch (Fixed): Error in loadHeater:', error);
            // Load from backup if any error occurs
            await this.loadBackupDataForDetail();
          }
        };

        // Add method to load detail data from backup
        WaterHeaterDetail.prototype.loadBackupDataForDetail = async function() {
          try {
            const backupUrl = '/static/data/water_heaters_backup.json';
            console.log('Water Heater Patch (Fixed): Loading detail from backup:', backupUrl);

            const response = await fetch(backupUrl);
            if (response.ok) {
              const backupData = await response.json();

              // Find this water heater in the backup data
              const backupHeater = backupData.find(h => h.id === this.heaterId);
              if (backupHeater) {
                console.log(`Water Heater Patch (Fixed): Found water heater ${this.heaterId} in backup`);

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
                console.warn(`Water Heater Patch (Fixed): Water heater ${this.heaterId} not found in backup`);
              }
            } else {
              console.warn(`Water Heater Patch (Fixed): Failed to load backup data: ${response.status} ${response.statusText}`);
            }
          } catch (error) {
            console.error('Water Heater Patch (Fixed): Error loading backup data:', error);
          }

          return false;
        };
      }

      console.log('Water Heater Patch (Fixed): Initialization complete');
    } else {
      console.warn('Water Heater Patch (Fixed): WaterHeaterList class not found, patch not applied');
    }
  }, 500); // Wait 500ms to ensure classes are loaded
});
