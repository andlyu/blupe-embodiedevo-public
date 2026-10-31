import type {Metadata} from 'next';
import './globals.css';
export const metadata:Metadata={title:'BluPe × EmbodiedEvo — Real YAM skills',description:'Reuse EmbodiedEvo skills learned in simulation and run them directly on BluPe Remote YAM.',icons:{icon:'/favicon.svg'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>;}
