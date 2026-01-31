import { Search, Lightbulb, User, CheckCircle, Play } from 'lucide-react';
import { Button } from '../ui/button';
import FeaturePill from './FeaturePill';
import laptopIllustration from '../../assets/laptop-illustration.png';
import videoLearningIllustration from '../../assets/video-learning-illustration.png';

const HeroSection = () => {
    return (
        <main className="max-w-7xl mx-auto px-6 pt-12 pb-24 text-center">
            {/* Hero Content */}
            <div className="mb-12">
                <h1 className="text-5xl md:text-6xl font-bold text-foreground tracking-tight mb-4">
                    Learn from YouTube videos,
                    <br />
                    <span className="hero-gradient-text">the smart way.</span>
                </h1>
                <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                    Transform YouTube videos into interactive learning experiences with
                    AI that extracts key concepts, answers your questions, and
                    creates personalized quizzes.
                </p>
            </div>

            {/* Hero Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20">
                <Button variant="hero" size="lg">
                    Get Started
                </Button>
                <Button variant="outline" size="lg">
                    See How It Works
                </Button>
            </div>

            {/* Hero Illustrations */}
            <div className="relative max-w-5xl mx-auto mb-24">
                {/* Left illustration */}
                <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 md:-translate-x-12 w-48 md:w-72 z-0">
                    <img
                        src={videoLearningIllustration}
                        alt="Video learning illustration"
                        className="w-full h-auto"
                    />
                </div>

                {/* Center laptop */}
                <div className="relative z-10 max-w-2xl mx-auto">
                    <img
                        src={laptopIllustration}
                        alt="Learning platform interface"
                        className="w-full h-auto"
                    />
                </div>
            </div>

            {/* Feature Pills */}
            <div className="flex flex-wrap justify-center gap-4">
                <FeaturePill icon={Search} label="Query YouTube" variant="teal" />
                <FeaturePill icon={Lightbulb} label="Interactive Quizzes" variant="yellow" />
                <FeaturePill icon={User} label="Personalized Learning" variant="purple" />
                <FeaturePill icon={CheckCircle} label="Precise Answers" variant="blue" />
                <FeaturePill icon={Play} label="Timestamps" variant="green" />
            </div>

            {/* Background decorations */}
            <div className="fixed top-0 left-0 -z-10 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/5 rounded-full blur-3xl" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent/5 rounded-full blur-3xl" />
            </div>
        </main>
    );
};

export default HeroSection;
