package main

import (
	"fmt"
	"os"
	"runtime"
)

func main() {
	hostname, _ := os.Hostname()
	fmt.Printf("Hello from %s!\n", hostname)
	fmt.Printf("Running on %s/%s\n", runtime.GOOS, runtime.GOARCH)
	fmt.Printf("Built with Go %s\n", runtime.Version())
}
