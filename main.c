#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

// Embedded image data - this will be replaced by the build script
unsigned char embedded_image[] = {
    // This will be filled by the build script
    0x00
};

unsigned int embedded_image_size = 0;

int main() {
    char tempPath[MAX_PATH];
    char tempFileName[MAX_PATH];
    
    // Get temporary directory
    if (GetTempPathA(MAX_PATH, tempPath) == 0) {
        return 1;
    }
    
    // Create temporary file name
    if (GetTempFileNameA(tempPath, "wall", 0, tempFileName) == 0) {
        return 1;
    }
    
    // Write embedded image to temporary file
    FILE *file = fopen(tempFileName, "wb");
    if (!file) {
        return 1;
    }
    
    fwrite(embedded_image, 1, embedded_image_size, file);
    fclose(file);
    
    // Convert the path to wide string (Unicode) as required by Windows API
    int widePathLen = MultiByteToWideChar(CP_UTF8, 0, tempFileName, -1, NULL, 0);
    if (widePathLen == 0) {
        DeleteFileA(tempFileName);
        return 1;
    }
    
    wchar_t *widePath = (wchar_t *)malloc(widePathLen * sizeof(wchar_t));
    if (!widePath) {
        DeleteFileA(tempFileName);
        return 1;
    }
    
    if (MultiByteToWideChar(CP_UTF8, 0, tempFileName, -1, widePath, widePathLen) == 0) {
        free(widePath);
        DeleteFileA(tempFileName);
        return 1;
    }
    
    // Change the wallpaper using SystemParametersInfo
    BOOL result = SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,  // Action: set desktop wallpaper
        0,                      // Not used for this action
        widePath,              // Path to the image file
        SPIF_UPDATEINIFILE | SPIF_SENDCHANGE  // Update registry and notify system
    );
    
    // Clean up
    free(widePath);
    DeleteFileA(tempFileName);
    
    return result ? 0 : 1;
}
