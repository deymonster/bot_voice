import asyncio
from concurrent.futures import ThreadPoolExecutor
from faster_whisper import WhisperModel
from loguru import logger
from app.config import Config

class AudioTranscriber:
    def __init__(self):
        logger.info(f"Loading Whisper model: {Config.MODEL_SIZE} on {Config.DEVICE} with {Config.COMPUTE_TYPE}...")
        try:
            self.model = WhisperModel(
                Config.MODEL_SIZE,
                device=Config.DEVICE,
                compute_type=Config.COMPUTE_TYPE,
                download_root="models",
                local_files_only=Config.LOCAL_FILES_ONLY,
                cpu_threads=Config.CPU_THREADS,
                num_workers=Config.NUM_WORKERS
            )
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise e
        
        # Create a thread pool executor for running CPU-bound transcription tasks
        # This acts as our "Queue" with concurrency limit
        self.executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS)

    def shutdown(self):
        """
        Gracefully shuts down the executor, waiting for pending tasks to complete.
        """
        logger.info("Shutting down Transcriber Executor...")
        self.executor.shutdown(wait=True)
        logger.info("Transcriber Executor shut down successfully.")

    def _transcribe_sync(self, file_path: str) -> str:
        """
        Synchronous method to run transcription.
        Running this in the main thread would block the bot.
        """
        try:
            logger.info(f"Starting transcription for {file_path}")
            segments, info = self.model.transcribe(
                file_path,
                beam_size=Config.BEAM_SIZE,
                language="ru",
                vad_filter=Config.VAD_FILTER,
                temperature=0.0,
                initial_prompt=Config.INITIAL_PROMPT or None,
                no_speech_threshold=Config.NO_SPEECH_THRESHOLD,
                without_timestamps=Config.WITHOUT_TIMESTAMPS,
                condition_on_previous_text=Config.CONDITION_ON_PREVIOUS_TEXT
            )
            
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text)
            
            full_text = " ".join(text_segments).strip()
            logger.info(f"Transcription finished. Language: {info.language}, Probability: {info.language_probability:.2f}")
            return full_text
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return f"Error: {str(e)}"

    async def transcribe(self, file_path: str) -> str:
        """
        Asynchronous wrapper around the synchronous transcription.
        """
        loop = asyncio.get_running_loop()
        # Run the CPU-bound task in the thread pool
        result = await loop.run_in_executor(
            self.executor, 
            self._transcribe_sync, 
            file_path
        )
        return result
