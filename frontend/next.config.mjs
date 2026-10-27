// frontend/next.config.js

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  
  // Paquetes que necesitan transpilación
  transpilePackages: ["three", "@react-three/fiber", "@react-three/drei"],
  
  // Configuración de webpack
  webpack: (config) => {
    // Suppress canvas/encoding warnings from PixiJS optional deps
    config.resolve.fallback = { 
      ...config.resolve.fallback, 
      canvas: false, 
      encoding: false 
    };
    return config;
  },
  
  // Aumentar el límite de tamaño para las peticiones API
  experimental: {
    serverActions: {
      bodySizeLimit: '50mb',
    },
  },
  
  // ✅ Configuración de imágenes (UNIFICADA)
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '9000',
        pathname: '/**',
      },
      {
        protocol: 'http',
        hostname: 'minio',
        port: '9000',
        pathname: '/**',
      },
      {
        protocol: 'http',
        hostname: '127.0.0.1',
        port: '9000',
        pathname: '/**',
      },
    ],
  },
};

export default nextConfig;