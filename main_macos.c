#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <pwd.h>

// Embedded image data - this will be replaced by the build script
unsigned char embedded_image[] = {
    // This will be filled by the build script
    0x00
};

unsigned int embedded_image_size = 0;

int main() {
    char tempPath[256];
    char tempFileName[512];
    
    // Get temporary directory
    const char *tmpdir = getenv("TMPDIR");
    if (!tmpdir) {
        tmpdir = "/tmp";
    }
    
    // Create temporary file name
    snprintf(tempFileName, sizeof(tempFileName), "%s/wallpaper_XXXXXX.png", tmpdir);
    int fd = mkstemp(tempFileName);
    if (fd == -1) {
        return 1;
    }
    close(fd);
    
    // Write embedded image to temporary file
    FILE *file = fopen(tempFileName, "wb");
    if (!file) {
        unlink(tempFileName);
        return 1;
    }
    
    fwrite(embedded_image, 1, embedded_image_size, file);
    fclose(file);
    
    // Use macOS command to change wallpaper
    char command[1024];
    snprintf(command, sizeof(command), 
             "osascript -e 'tell application \"System Events\" to tell every desktop to set picture to \"%s\"'", 
             tempFileName);
    
    int result = system(command);
    
    // Clean up
    unlink(tempFileName);
    
    return (result == 0) ? 0 : 1;
} 