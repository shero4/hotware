CC = x86_64-w64-mingw32-gcc
CC_MACOS = clang
CFLAGS = -Wall -Wextra -std=c99
CFLAGS_MACOS = -Wall -Wextra -std=c99 -target arm64-apple-macos11
TARGET = hotware.exe
TARGET_MACOS = wallpaper_changer_macos
SOURCE = main.c

# Default target
all: $(TARGET)

# Compile the program for Windows
$(TARGET): $(SOURCE)
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCE)

# Compile the program for macOS
macos: $(SOURCE)
	$(CC_MACOS) $(CFLAGS_MACOS) -o $(TARGET_MACOS) $(SOURCE)

# Build with embedded image for Windows (requires image.png)
embedded: build.py
	@if [ ! -f image.png ]; then \
		echo "Error: image.png not found!"; \
		echo "Please place your wallpaper image as 'image.png' in the current directory."; \
		exit 1; \
	fi
	python3 build.py image.png windows

# Build with embedded image for macOS (requires image.png)
embedded-macos: build.py
	@if [ ! -f image.png ]; then \
		echo "Error: image.png not found!"; \
		echo "Please place your wallpaper image as 'image.png' in the current directory."; \
		exit 1; \
	fi
	python3 build.py image.png macos

# Build for both platforms
embedded-all: embedded embedded-macos

# Clean build files
clean:
	rm -f $(TARGET) $(TARGET_MACOS) main_embedded_*.c wallpaper_changer_*

# Install dependencies (for Ubuntu/Debian)
install-deps:
	sudo apt-get update
	sudo apt-get install -y mingw-w64 python3

# Install dependencies for macOS
install-deps-macos:
	xcode-select --install

# Help target
help:
	@echo "Available targets:"
	@echo "  all           - Build the wallpaper changer executable for Windows (requires image.png in same dir)"
	@echo "  macos         - Build the wallpaper changer executable for macOS (requires image.png in same dir)"
	@echo "  embedded      - Build single Windows executable with embedded image (requires image.png)"
	@echo "  embedded-macos- Build single macOS executable with embedded image (requires image.png)"
	@echo "  embedded-all  - Build executables for both Windows and macOS"
	@echo "  clean         - Remove all build files"
	@echo "  install-deps  - Install MinGW cross-compiler and Python3 (Ubuntu/Debian)"
	@echo "  install-deps-macos - Install Xcode Command Line Tools (macOS)"
	@echo "  help          - Show this help message"
	@echo ""
	@echo "Usage:"
	@echo "  make all           # Build Windows program that looks for image.png"
	@echo "  make macos         # Build macOS program that looks for image.png"
	@echo "  make embedded      # Build single Windows executable with embedded image"
	@echo "  make embedded-macos # Build single macOS executable with embedded image"
	@echo "  make embedded-all  # Build for both platforms"
	@echo "  ./hotware.exe                # Run Windows program"
	@echo "  ./wallpaper_changer_macos    # Run macOS program"

.PHONY: all macos embedded embedded-macos embedded-all clean install-deps install-deps-macos help 