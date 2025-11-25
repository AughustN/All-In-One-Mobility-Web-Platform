import React from 'react';

export const BackgroundMap: React.FC = () => {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none z-0 bg-black">
      {/* Grid Pattern */}
      <div 
        className="absolute inset-0 opacity-[0.15]" 
        style={{
          backgroundImage: `linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)`,
          backgroundSize: '40px 40px'
        }}
      ></div>

      {/* Radial Gradient overlay for focus */}
      <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-black opacity-80"></div>
      <div className="absolute inset-0 bg-gradient-to-r from-black via-transparent to-black opacity-80"></div>

      {/* Abstract Map Lines - Stylized Vietnam Coastline concept */}
      <svg className="absolute right-0 top-0 h-full w-full md:w-2/3 opacity-20 text-zinc-700" viewBox="0 0 400 800" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path 
          d="M100 50 C 150 100, 200 150, 180 200 C 160 250, 120 300, 140 350 C 160 400, 220 450, 200 500 C 180 550, 100 650, 120 750" 
          stroke="currentColor" 
          strokeWidth="2"
          className="animate-pulse-slow"
        />
         <path 
          d="M120 50 C 170 100, 220 150, 200 200 C 180 250, 140 300, 160 350 C 180 400, 240 450, 220 500 C 200 550, 120 650, 140 750" 
          stroke="currentColor" 
          strokeWidth="1"
          strokeDasharray="5 5"
          className="opacity-50"
        />
        {/* Decorative Circles representing cities */}
        <circle cx="180" cy="200" r="3" fill="white" className="animate-ping" style={{animationDuration: '3s'}} />
        <circle cx="140" cy="350" r="3" fill="white" className="animate-ping" style={{animationDuration: '4s', animationDelay: '1s'}} />
        <circle cx="200" cy="500" r="3" fill="white" className="animate-ping" style={{animationDuration: '3s', animationDelay: '2s'}} />
      </svg>
      
      {/* Glow Effect */}
      <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-zinc-800 rounded-full mix-blend-screen filter blur-[128px] opacity-20 animate-pulse"></div>
    </div>
  );
};