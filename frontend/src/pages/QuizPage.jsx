import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  HelpCircle,
  Sparkles,
  CheckCircle2,
  XCircle,
  ArrowRight,
  RotateCcw,
  BookOpen,
  Award,
  AlertCircle,
} from 'lucide-react';
import { useResources } from '../hooks/useResources';
import { useQuizzes, useGenerateQuiz, useDeleteQuizzes } from '../hooks/useStudy';
import { useSubmitQuizResult } from '../hooks/useMastery';
import { AppLayout } from '../components/layout/AppLayout';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { ResourceStudyHeader } from '../components/study/ResourceStudyHeader';

export function QuizPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const queryResourceId = searchParams.get('resource_id') || '';
  const { data: resources = [], isLoading: isLoadingResources } = useResources();

  const [selectedResourceId, setSelectedResourceId] = useState(queryResourceId);
  const [difficulty, setDifficulty] = useState('medium');
  const [questionCount, setQuestionCount] = useState(5);

  useEffect(() => {
    if (!selectedResourceId && resources.length > 0) {
      setSelectedResourceId(resources[0].resource_id);
    }
  }, [resources, selectedResourceId]);

  const { data: quizzes = [], isLoading: isLoadingQuizzes } = useQuizzes(selectedResourceId);
  const generateQuizMutation = useGenerateQuiz();
  const deleteQuizzesMutation = useDeleteQuizzes();
  const submitQuizMutation = useSubmitQuizResult();

  const selectedResource = resources.find((r) => r.resource_id === selectedResourceId);

  // Runner state
  const [currentQuiz, setCurrentQuiz] = useState(null);
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [submittedQuestions, setSubmittedQuestions] = useState({});
  const [quizCompleted, setQuizCompleted] = useState(false);

  useEffect(() => {
    if (quizzes.length > 0) {
      setCurrentQuiz(quizzes[0]);
    } else {
      setCurrentQuiz(null);
    }
  }, [quizzes]);

  const handleSelectResource = (resId) => {
    setSelectedResourceId(resId);
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      if (resId) p.set('resource_id', resId);
      else p.delete('resource_id');
      return p;
    });
  };

  const handleGenerateQuiz = async () => {
    if (!selectedResourceId) return;
    try {
      const newQuiz = await generateQuizMutation.mutateAsync({
        resourceId: selectedResourceId,
        questionCount: parseInt(questionCount, 10),
        difficulty,
      });
      setCurrentQuiz(newQuiz);
      setUserAnswers({});
      setSubmittedQuestions({});
      setQuizCompleted(false);
    } catch {
      // Toast handles error
    }
  };

  const handleDeleteQuizzes = async () => {
    if (!selectedResourceId) return;
    try {
      await deleteQuizzesMutation.mutateAsync({
        resourceId: selectedResourceId,
        quizId: currentQuiz?.id,
      });
      setCurrentQuiz(null);
      setUserAnswers({});
      setSubmittedQuestions({});
      setQuizCompleted(false);
    } catch {
      // Toast handles error
    }
  };

  const handleSelectOption = (optionIdx) => {
    if (submittedQuestions[currentQuestionIdx]) return; // locked once submitted
    setUserAnswers((prev) => ({
      ...prev,
      [currentQuestionIdx]: optionIdx,
    }));
  };

  const handleSubmitAnswer = () => {
    if (userAnswers[currentQuestionIdx] === undefined) return;
    setSubmittedQuestions((prev) => ({
      ...prev,
      [currentQuestionIdx]: true,
    }));
  };

  const handleNext = () => {
    if (!questions) return;
    if (currentQuestionIdx < questions.length - 1) {
      setCurrentQuestionIdx((prev) => prev + 1);
    } else {
      setQuizCompleted(true);
      if (currentQuiz?.id) {
        submitQuizMutation.mutateAsync({
          quizId: currentQuiz.id,
          score: correctCount,
          totalQuestions: questions.length,
        }).catch((err) => console.error('Failed to submit quiz attempt:', err));
      }
    }
  };

  const handlePrev = () => {
    if (currentQuestionIdx > 0) {
      setCurrentQuestionIdx((prev) => prev - 1);
    }
  };

  const handleRestartQuiz = () => {
    setCurrentQuestionIdx(0);
    setUserAnswers({});
    setSubmittedQuestions({});
    setQuizCompleted(false);
  };

  // Parse questions from backend QuizResponse schema or questions_json
  let questions = [];
  if (currentQuiz) {
    if (Array.isArray(currentQuiz.questions) && currentQuiz.questions.length > 0) {
      questions = currentQuiz.questions;
    } else if (currentQuiz.questions_json) {
      try {
        questions =
          typeof currentQuiz.questions_json === 'string'
            ? JSON.parse(currentQuiz.questions_json)
            : currentQuiz.questions_json || [];
      } catch {
        questions = [];
      }
    }
  }

  // Calculate final score
  let correctCount = 0;
  if (questions.length > 0) {
    questions.forEach((q, idx) => {
      if (userAnswers[idx] === q.correct_answer_index) {
        correctCount += 1;
      }
    });
  }

  const scorePercentage = questions.length > 0 ? Math.round((correctCount / questions.length) * 100) : 0;

  return (
    <AppLayout title="Practice Quiz">
      {/* Resource Context & Navigation Header */}
      <ResourceStudyHeader
        activeTab="quiz"
        selectedResource={selectedResource}
        onRegenerate={handleGenerateQuiz}
        onDeleteContent={currentQuiz ? handleDeleteQuizzes : null}
        isDeleteLoading={deleteQuizzesMutation.isPending}
        deleteTitle="Delete Generated Quiz?"
        deleteMessage="This will permanently remove the generated quiz for this resource. You can regenerate a new quiz anytime."
      />

      {/* Quiz Config Bar */}
      <Card className="mb-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4 text-xs font-semibold text-slate-700 dark:text-slate-300">
            <div className="flex items-center gap-2">
              <span className="uppercase text-[11px] text-slate-400">Questions:</span>
              <select
                value={questionCount}
                onChange={(e) => setQuestionCount(Number(e.target.value))}
                className="bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg p-1.5 focus:outline-none"
              >
                <option value={3}>3 Questions</option>
                <option value={5}>5 Questions</option>
                <option value={10}>10 Questions</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="uppercase text-[11px] text-slate-400">Difficulty:</span>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg p-1.5 focus:outline-none"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>

          <Button
            variant="primary"
            size="sm"
            icon={Sparkles}
            onClick={handleGenerateQuiz}
            isLoading={generateQuizMutation.isPending}
            disabled={!selectedResourceId}
          >
            Generate New Quiz
          </Button>
        </div>
      </Card>

      {/* Content Area */}
      {!selectedResourceId ? (
        <Card className="text-center py-12">
          <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400 mx-auto flex items-center justify-center mb-3">
            <HelpCircle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">No Resource Selected</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4">
            Select a study material above to start generating practice quizzes.
          </p>
        </Card>
      ) : generateQuizMutation.isPending || isLoadingQuizzes ? (
        <Card className="p-8 space-y-4">
          <Skeleton className="h-4 w-32 mb-2" />
          <Skeleton className="h-6 w-full mb-6" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </Card>
      ) : !currentQuiz || questions.length === 0 ? (
        <Card className="text-center py-12">
          <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400 mx-auto flex items-center justify-center mb-3">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">No Quiz Available</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-6">
            Generate your first interactive AI practice quiz for "{selectedResource?.title || selectedResource?.source}".
          </p>
          <Button variant="primary" size="md" icon={Sparkles} onClick={handleGenerateQuiz}>
            Generate Quiz
          </Button>
        </Card>
      ) : quizCompleted ? (
        /* Quiz Completion Final Score Screen */
        <Card className="max-w-lg mx-auto text-center p-8">
          <div className="w-16 h-16 rounded-3xl bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400 mx-auto flex items-center justify-center mb-4 shadow-sm">
            <Award className="w-8 h-8" />
          </div>
          <h3 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100">Quiz Completed!</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-6">
            Review your final score for "{selectedResource?.title || selectedResource?.source}".
          </p>

          <div className="bg-slate-50 dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-700/80 mb-6">
            <div className="text-4xl font-extrabold text-blue-600 dark:text-blue-400">
              {scorePercentage}%
            </div>
            <p className="text-xs font-semibold text-slate-600 dark:text-slate-300 mt-1">
              You answered {correctCount} out of {questions.length} questions correctly.
            </p>
          </div>

          <div className="flex justify-center gap-3">
            <Button variant="secondary" size="md" icon={RotateCcw} onClick={handleRestartQuiz}>
              Retry Quiz
            </Button>
            <Button variant="primary" size="md" icon={Sparkles} onClick={handleGenerateQuiz}>
              Generate New Quiz
            </Button>
          </div>
        </Card>
      ) : (
        /* Active Question Card */
        <Card className="max-w-2xl mx-auto p-6 md:p-8">
          {/* Progress Bar & Progress Badge */}
          <div className="flex items-center justify-between mb-3 text-xs text-slate-500 dark:text-slate-400 font-semibold">
            <span>
              Question {currentQuestionIdx + 1} of {questions.length}
            </span>
            <Badge variant="warning" className="uppercase">
              Difficulty: {difficulty}
            </Badge>
          </div>

          <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full mb-6 overflow-hidden">
            <div
              className="bg-blue-600 h-full transition-all duration-300"
              style={{ width: `${((currentQuestionIdx + 1) / questions.length) * 100}%` }}
            />
          </div>

          {/* Current Question Text */}
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-6">
            {questions[currentQuestionIdx]?.question}
          </h3>

          {/* Option Choices List */}
          <div className="space-y-3 mb-6">
            {questions[currentQuestionIdx]?.options.map((option, optIdx) => {
              const isSelected = userAnswers[currentQuestionIdx] === optIdx;
              const isSubmitted = submittedQuestions[currentQuestionIdx];
              const isCorrect = questions[currentQuestionIdx]?.correct_answer_index === optIdx;

              let optionStyle =
                'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 hover:border-blue-400';

              // CRITICAL RULE: Reveal correct/incorrect status ONLY after user submits answer!
              if (isSubmitted) {
                if (isCorrect) {
                  optionStyle =
                    'border-green-500 bg-green-50 dark:bg-green-950/60 text-green-900 dark:text-green-100 font-semibold';
                } else if (isSelected) {
                  optionStyle =
                    'border-red-500 bg-red-50 dark:bg-red-950/60 text-red-900 dark:text-red-100 font-semibold';
                } else {
                  optionStyle = 'border-slate-200 dark:border-slate-700/50 opacity-60';
                }
              } else if (isSelected) {
                optionStyle =
                  'border-blue-600 bg-blue-50 dark:bg-blue-950/60 text-blue-900 dark:text-blue-100 font-semibold ring-2 ring-blue-500/20';
              }

              return (
                <div
                  key={optIdx}
                  onClick={() => handleSelectOption(optIdx)}
                  className={`p-4 rounded-xl border text-sm flex items-center justify-between cursor-pointer transition-all ${optionStyle}`}
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-700 font-bold text-xs flex items-center justify-center shrink-0">
                      {String.fromCharCode(65 + optIdx)}
                    </span>
                    <span>{option}</span>
                  </div>

                  {isSubmitted && (
                    <div>
                      {isCorrect ? (
                        <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400 shrink-0" />
                      ) : isSelected ? (
                        <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 shrink-0" />
                      ) : null}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Explanation Box (Hidden until submitted) */}
          {submittedQuestions[currentQuestionIdx] && questions[currentQuestionIdx]?.explanation && (
            <div className="p-4 rounded-xl bg-blue-50/50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800/60 mb-6 text-xs leading-relaxed">
              <span className="font-bold text-blue-700 dark:text-blue-300 block mb-1">
                Explanation:
              </span>
              <p className="text-slate-700 dark:text-slate-300">
                {questions[currentQuestionIdx].explanation}
              </p>
            </div>
          )}

          {/* Question Footer Actions */}
          <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-700/50">
            <Button
              variant="outline"
              size="sm"
              icon={ArrowLeft}
              onClick={handlePrev}
              disabled={currentQuestionIdx === 0}
            >
              Previous
            </Button>

            {!submittedQuestions[currentQuestionIdx] ? (
              <Button
                variant="primary"
                size="sm"
                onClick={handleSubmitAnswer}
                disabled={userAnswers[currentQuestionIdx] === undefined}
              >
                Submit Answer
              </Button>
            ) : (
              <Button variant="primary" size="sm" onClick={handleNext}>
                <span>
                  {currentQuestionIdx === questions.length - 1 ? 'Finish Quiz' : 'Next Question'}
                </span>
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            )}
          </div>
        </Card>
      )}
    </AppLayout>
  );
}
