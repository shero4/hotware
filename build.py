#!/usr/bin/env python3
import os
import sys
import subprocess
import struct
import platform

def embed_image(image_path, output_c_file="main_embedded.c", platform_type="windows"):
    """Embed image data into C source code"""
    
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found!")
        return False
    
    # Read the image file
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    if platform_type == "macos":
        # Generate macOS C code with embedded image
        c_code = f'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <pwd.h>

// Embedded image data
unsigned char embedded_image[] = {{
    {', '.join(f'0x{b:02x}' for b in image_data)}
}};

unsigned int embedded_image_size = {len(image_data)};

int main() {{
    char tempPath[256];
    char tempFileName[512];
    
    // Get temporary directory
    const char *tmpdir = getenv("TMPDIR");
    if (!tmpdir) {{
        tmpdir = "/tmp";
    }}
    
    // Create temporary file name
    snprintf(tempFileName, sizeof(tempFileName), "%s/wallpaper_XXXXXX.png", tmpdir);
    int fd = mkstemp(tempFileName);
    if (fd == -1) {{
        return 1;
    }}
    close(fd);
    
    // Write embedded image to temporary file
    FILE *file = fopen(tempFileName, "wb");
    if (!file) {{
        unlink(tempFileName);
        return 1;
    }}
    
    fwrite(embedded_image, 1, embedded_image_size, file);
    fclose(file);
    
    // Use macOS command to change wallpaper
    char command[1024];
    snprintf(command, sizeof(command), 
             "osascript -e 'tell application \\"System Events\\" to tell every desktop to set picture to \\"%s\\"'", 
             tempFileName);
    
    int result = system(command);
    
    // Clean up
    unlink(tempFileName);
    
    return (result == 0) ? 0 : 1;
}}
'''
    else:
        # Generate Windows C code with embedded image
        c_code = f'''#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

// Embedded image data
unsigned char embedded_image[] = {{
    {', '.join(f'0x{b:02x}' for b in image_data)}
}};

unsigned int embedded_image_size = {len(image_data)};

int main() {{
    char tempPath[MAX_PATH];
    char tempFileName[MAX_PATH];
    
    // Get temporary directory
    if (GetTempPathA(MAX_PATH, tempPath) == 0) {{
        return 1;
    }}
    
    // Create temporary file name
    if (GetTempFileNameA(tempPath, "wall", 0, tempFileName) == 0) {{
        return 1;
    }}
    
    // Write embedded image to temporary file
    FILE *file = fopen(tempFileName, "wb");
    if (!file) {{
        return 1;
    }}
    
    fwrite(embedded_image, 1, embedded_image_size, file);
    fclose(file);
    
    // Convert the path to wide string (Unicode) as required by Windows API
    int widePathLen = MultiByteToWideChar(CP_UTF8, 0, tempFileName, -1, NULL, 0);
    if (widePathLen == 0) {{
        DeleteFileA(tempFileName);
        return 1;
    }}
    
    wchar_t *widePath = (wchar_t *)malloc(widePathLen * sizeof(wchar_t));
    if (!widePath) {{
        DeleteFileA(tempFileName);
        return 1;
    }}
    
    if (MultiByteToWideChar(CP_UTF8, 0, tempFileName, -1, widePath, widePathLen) == 0) {{
        free(widePath);
        DeleteFileA(tempFileName);
        return 1;
    }}
    
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
}}
'''
    
    # Write the generated C code
    with open(output_c_file, 'w') as f:
        f.write(c_code)
    
    print(f"Generated {output_c_file} with embedded image ({len(image_data)} bytes)")
    return True

def compile_executable(c_file, output_exe="hotware", platform_type="windows"):
    """Compile the C file to an executable"""
    
    if platform_type == "macos":
        # Check if we're on macOS or if we have cross-compilation tools
        current_platform = detect_platform()
        
        if current_platform == "macos":
            # We're on macOS, use clang
            try:
                result = subprocess.run(['clang', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    print("Error: clang compiler not found!")
                    print("Please install Xcode Command Line Tools:")
                    print("xcode-select --install")
                    return False
            except FileNotFoundError:
                print("Error: clang compiler not found!")
                print("Please install Xcode Command Line Tools:")
                print("xcode-select --install")
                return False
            
            # Compile for macOS (Apple Silicon)
            cmd = [
                'clang',
                '-Wall', '-Wextra', '-std=c99',
                '-target', 'arm64-apple-macos11',  # Target Apple Silicon
                '-o', output_exe,
                c_file
            ]
            
            print(f"Compiling {c_file} to {output_exe} for macOS (Apple Silicon)...")
            
        else:
            # We're on Linux/Windows, check for macOS cross-compiler
            try:
                result = subprocess.run(['x86_64-apple-darwin20-clang', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # Use cross-compiler
                    cmd = [
                        'x86_64-apple-darwin20-clang',
                        '-Wall', '-Wextra', '-std=c99',
                        '-target', 'arm64-apple-macos11',
                        '-o', output_exe,
                        c_file
                    ]
                    print(f"Cross-compiling {c_file} to {output_exe} for macOS (Apple Silicon)...")
                else:
                    print("Error: macOS cross-compiler not found!")
                    print("To compile for macOS from Linux, you need:")
                    print("1. Install osxcross: https://github.com/tpoechtrager/osxcross")
                    print("2. Or compile directly on a macOS machine")
                    print("3. Or use the generated C source file on macOS")
                    print(f"\nGenerated source file: {c_file}")
                    print("You can copy this file to a macOS machine and compile with:")
                    print(f"clang -Wall -Wextra -std=c99 -target arm64-apple-macos11 -o {output_exe} {c_file}")
                    return False
            except FileNotFoundError:
                print("Error: macOS cross-compiler not found!")
                print("To compile for macOS from Linux, you need:")
                print("1. Install osxcross: https://github.com/tpoechtrager/osxcross")
                print("2. Or compile directly on a macOS machine")
                print("3. Or use the generated C source file on macOS")
                print(f"\nGenerated source file: {c_file}")
                print("You can copy this file to a macOS machine and compile with:")
                print(f"clang -Wall -Wextra -std=c99 -target arm64-apple-macos11 -o {output_exe} {c_file}")
                return False
        
    else:
        # Check if MinGW is available
        try:
            result = subprocess.run(['x86_64-w64-mingw32-gcc', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("Error: MinGW cross-compiler not found!")
                print("Please install it with: sudo apt-get install mingw-w64")
                return False
        except FileNotFoundError:
            print("Error: MinGW cross-compiler not found!")
            print("Please install it with: sudo apt-get install mingw-w64")
            return False
        
        # Compile for Windows
        cmd = [
            'x86_64-w64-mingw32-gcc',
            '-Wall', '-Wextra', '-std=c99',
            '-o', output_exe + '.exe',
            c_file
        ]
        
        print(f"Compiling {c_file} to {output_exe}.exe for Windows...")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Compilation failed!")
        print("Error:", result.stderr)
        return False
    
    if platform_type == "macos":
        print(f"Successfully created {output_exe}")
    else:
        print(f"Successfully created {output_exe}.exe")
    return True

def detect_platform():
    """Detect the current platform"""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 build.py <image_file> [platform]")
        print("Example: python3 build.py wallpaper.png")
        print("Example: python3 build.py wallpaper.png macos")
        print("Example: python3 build.py wallpaper.png windows")
        print("\nPlatforms: macos, windows (auto-detected if not specified)")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Determine platform
    if len(sys.argv) > 2:
        platform_type = sys.argv[2].lower()
        if platform_type not in ["macos", "windows"]:
            print("Error: Invalid platform. Use 'macos' or 'windows'")
            sys.exit(1)
    else:
        platform_type = detect_platform()
        if platform_type == "unknown":
            print("Error: Could not detect platform. Please specify: macos or windows")
            sys.exit(1)
        print(f"Auto-detected platform: {platform_type}")
    
    # Step 1: Embed the image
    if not embed_image(image_path, f"main_embedded_{platform_type}.c", platform_type):
        sys.exit(1)
    
    # Step 2: Compile the executable
    if platform_type == "windows":
        output_name = "hotware"
    else:
        output_name = f"wallpaper_changer_{platform_type}"
    if compile_executable(f"main_embedded_{platform_type}.c", output_name, platform_type):
        print(f"\nBuild completed successfully for {platform_type}!")
        if platform_type == "macos":
            print("You can now run the executable on any macOS computer to change the wallpaper.")
        else:
            print("You can now run the executable on any Windows computer to change the wallpaper.")
    else:
        if platform_type == "macos":
            print(f"\nSource file generated: main_embedded_{platform_type}.c")
            print("To compile on macOS, copy this file to a Mac and run:")
            print(f"clang -Wall -Wextra -std=c99 -target arm64-apple-macos11 -o wallpaper_changer_macos main_embedded_{platform_type}.c")
        else:
            sys.exit(1)

if __name__ == "__main__":
    main() 