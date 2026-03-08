import RadioPlayer from './components/RadioPlayer.jsx';

export default function RadioPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-900 p-6">
      <div className="w-full max-w-lg">
        <h1 className="text-2xl font-bold text-center text-white mb-6 tracking-wide opacity-80">
          🚌 MARTA Poetry Radio
        </h1>
        <RadioPlayer />
        <p className="text-center text-gray-500 text-xs mt-6">
          AI-generated poetry set to music, inspired by Atlanta's transit system.
        </p>
      </div>
    </div>
  );
}
