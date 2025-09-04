import React, { useState, useRef } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Button, 
  Grid, 
  Card, 
  CardContent, 
  Avatar, 
  Chip,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  useTheme,
  useMediaQuery,
  IconButton
} from '@mui/material';
import {
  Chat as ChatIcon,
  School as SchoolIcon,
  Quiz as QuizIcon,
  Psychology as PsychologyIcon,
  CheckCircle as CheckIcon,
  Star as StarIcon,
  ArrowForward as ArrowIcon,
  PlayArrow as PlayIcon,
  TrendingUp as TrendingIcon,
  Security as SecurityIcon,
  Support as SupportIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon
} from '@mui/icons-material';

interface HomePageProps {
  onGetStarted: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onGetStarted }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isLargeScreen = useMediaQuery(theme.breakpoints.up('lg'));
  const [activeTestimonial, setActiveTestimonial] = useState(0);
  const [currentCourseIndex, setCurrentCourseIndex] = useState(0);
  const coursesScrollRef = useRef<HTMLDivElement>(null);

  const features = [
    {
      icon: <ChatIcon sx={{ fontSize: 40, color: '#667eea' }} />,
      title: 'AI-Powered Chat',
      description: 'Get personalized financial advice from our intelligent AI assistant, available 24/7 to answer your questions.',
      color: '#667eea'
    },
    {
      icon: <SchoolIcon sx={{ fontSize: 40, color: '#764ba2' }} />,
      title: 'Interactive Courses',
      description: 'Learn essential financial skills through engaging, interactive courses designed for your learning style.',
      color: '#764ba2'
    },
    {
      icon: <QuizIcon sx={{ fontSize: 40, color: '#f093fb' }} />,
      title: 'Smart Quizzes',
      description: 'Test your knowledge with adaptive quizzes that help you understand and retain financial concepts.',
      color: '#f093fb'
    },
    {
      icon: <PsychologyIcon sx={{ fontSize: 40, color: '#4facfe' }} />,
      title: 'Personalized Advice',
      description: 'Receive tailored financial recommendations based on your unique situation and goals.',
      color: '#4facfe'
    }
  ];

  const learningProcess = [
    {
      step: '01',
      title: 'Sign Up',
      description: 'Create your account in seconds and start your financial journey.',
      icon: <CheckIcon />
    },
    {
      step: '02',
      title: 'Take Assessment',
      description: 'Complete a quick assessment to personalize your learning experience.',
      icon: <QuizIcon />
    },
    {
      step: '03',
      title: 'Start Learning',
      description: 'Access personalized courses, chat with AI, and track your progress.',
      icon: <SchoolIcon />

     
    }
  ];

  const courses = [
    {
      emoji: '🎯',
      title: 'Money, Goals and Mindset',
      description: 'Learn to set smart financial goals and develop a positive money mindset for your future',
      color: '#667eea'
    },
    {
      emoji: '💰',
      title: 'Budgeting and Saving',
      description: 'Master budgeting basics and build healthy saving habits for financial success',
      color: '#764ba2'
    },
    {
      emoji: '🎓',
      title: 'College Planning and Saving',
      description: 'Plan for college costs, find scholarships, and learn about student loans',
      color: '#f093fb'
    },
    {
      emoji: '💼',
      title: 'Earning and Income Basics',
      description: 'Understand paychecks, first jobs, and smart money habits when you start earning',
      color: '#4facfe'
    }
  ];



  const testimonials = [
    {
      name: 'Sarah Johnson',
      role: 'College Student',
      avatar: '👩‍🎓',
      content: 'MoneyMentor helped me understand budgeting and saving. The AI chat is incredibly helpful!',
      rating: 5
    },
    {
      name: 'Michael Chen',
      role: 'Young Professional',
      avatar: '👨‍💼',
      content: 'Finally, a financial education platform that speaks my language. The courses are practical and engaging.',
      rating: 5
    },
    {
      name: 'Emily Rodriguez',
      role: 'Graduate Student',
      avatar: '👩‍🎓',
      content: 'The personalized advice helped me pay off my student loans faster than I expected.',
      rating: 5
    }
  ];

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
      });
    }
  };

  const scrollCourses = (direction: 'left' | 'right') => {
    if (!coursesScrollRef.current) return;
    
    const container = coursesScrollRef.current;
    const cardWidth = container.children[0]?.clientWidth || 0;
    const gap = 24; // 24px gap between cards
    const scrollAmount = cardWidth + gap;
    
    if (direction === 'left') {
      container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
      setCurrentCourseIndex(Math.max(0, currentCourseIndex - 1));
    } else {
      container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
      setCurrentCourseIndex(Math.min(courses.length - 3, currentCourseIndex + 1));
    }
  };

  const handleWheelScroll = (e: React.WheelEvent) => {
    if (!coursesScrollRef.current) return;
    
    e.preventDefault();
    const container = coursesScrollRef.current;
    const cardWidth = container.children[0]?.clientWidth || 0;
    const gap = 24;
    const scrollAmount = cardWidth + gap;
    
    if (e.deltaY > 0) {
      // Scroll right
      container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
      setCurrentCourseIndex(Math.min(courses.length - 3, currentCourseIndex + 1));
    } else {
      // Scroll left
      container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
      setCurrentCourseIndex(Math.max(0, currentCourseIndex - 1));
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f8fafc' }}>
      {/* Hero Section */}
      <Box
        id="home"
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          py: { xs: 8, md: 12 },
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography
                variant="h2"
                component="h1"
                sx={{
                  fontWeight: 700,
                  mb: 2,
                  fontSize: { xs: '2.5rem', md: '3.5rem' },
                  lineHeight: 1.2
                }}
              >
                Master Your Money with AI
              </Typography>
              <Typography
                variant="h5"
                sx={{
                  mb: 4,
                  opacity: 0.9,
                  fontWeight: 300,
                  lineHeight: 1.4
                }}
              >
                Get personalized financial education powered by AI. Learn budgeting, investing, and debt management through interactive courses and smart quizzes.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={onGetStarted}
                  sx={{
                    bgcolor: 'white',
                    color: '#667eea',
                    px: 4,
                    py: 1.5,
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    '&:hover': {
                      bgcolor: '#f8f9fa',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 8px 25px rgba(0,0,0,0.15)'
                    },
                    transition: 'all 0.3s ease'
                  }}
                >
                  Get Started Free
                </Button>
                {/* <Button
                  variant="outlined"
                  size="large"
                  sx={{
                    borderColor: 'white',
                    color: 'white',
                    px: 4,
                    py: 1.5,
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    '&:hover': {
                      borderColor: 'white',
                      bgcolor: 'rgba(255,255,255,0.1)'
                    }
                  }}
                >
                  <PlayIcon sx={{ mr: 1 }} />
                  Watch Demo
                </Button> */}
              </Box>
              <Box sx={{ mt: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ display: 'flex' }}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <StarIcon key={star} sx={{ color: '#ffd700', fontSize: 20 }} />
                  ))}
                </Box>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Trusted by 10,000+ students and professionals
                </Typography>
              </Box>
            </Grid>
            {/* <Grid item xs={12} md={6}>
              <Box
                sx={{
                  position: 'relative',
                  height: { xs: 300, md: 400 },
                  bgcolor: 'rgba(255,255,255,0.1)',
                  borderRadius: 4,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255,255,255,0.2)'
                }}
              >
                <Typography variant="h4" sx={{ textAlign: 'center', opacity: 0.8 }}>
                  💰 AI Chat Demo
                </Typography>
              </Box>
            </Grid> */}
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Box id="features" sx={{ py: { xs: 8, md: 12 } }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography
              variant="h3"
              component="h2"
              sx={{
                fontWeight: 700,
                mb: 2,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Why Choose MoneyMentor?
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
              Our AI-powered platform combines cutting-edge technology with proven financial education methods
            </Typography>
          </Box>

          <Box sx={{ 
            display: 'flex', 
            gap: 3, 
            flexWrap: 'wrap',
            justifyContent: 'center',
            alignItems: 'stretch'
          }}>
            {features.map((feature, index) => (
              <Card
                key={index}
                sx={{
                  flex: '1 1 250px',
                  maxWidth: '280px',
                  minWidth: '250px',
                  p: 3,
                  textAlign: 'center',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: '0 12px 40px rgba(0,0,0,0.15)'
                  }
                }}
              >
                <Box sx={{ mb: 2 }}>
                  {feature.icon}
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {feature.description}
                </Typography>
              </Card>
            ))}
          </Box>
        </Container>
      </Box>

      {/* Learning Process Section */}
      <Box id="learning-process" sx={{ py: { xs: 8, md: 12 }, bgcolor: 'white' }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography
              variant="h3"
              component="h2"
              sx={{
                fontWeight: 700,
                mb: 2,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              Learning Process
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
              Start your personalized financial learning journey in 3 simple steps
            </Typography>
          </Box>

          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center',
            alignItems: 'flex-start',
            gap: 4,
            flexWrap: 'wrap',
            position: 'relative'
          }}>
            {learningProcess.map((step, index) => (
                              <Box 
                key={index} 
                sx={{ 
                  textAlign: 'center', 
                  position: 'relative',
                  flex: '1',
                  minWidth: '280px',
                  maxWidth: '320px',
                  width: '320px'
                }}
              >
                {/* Connecting line (except for last item) */}
                {index < learningProcess.length - 1 && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 40,
                      left: 'calc(100% + 16px)',
                      width: 'calc(100vw - 800px)',
                      maxWidth: '120px',
                      height: '2px',
                      background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                      zIndex: 0,
                      '@media (max-width: 1200px)': {
                        display: 'none'
                      }
                    }}
                  />
                )}
                
                {/* Step circle with enhanced styling */}
                <Box
                  sx={{
                    width: 80,
                    height: 80,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 3,
                    color: 'white',
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    position: 'relative',
                    zIndex: 1,
                    boxShadow: '0 8px 25px rgba(102, 126, 234, 0.3)',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'scale(1.1)',
                      boxShadow: '0 12px 35px rgba(102, 126, 234, 0.4)'
                    }
                  }}
                >
                  {step.step}
                </Box>
                
                {/* Content card */}
                <Box
                  sx={{
                    p: 3,
                    height: '200px',
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(248,250,252,0.9) 100%)',
                    border: '1px solid rgba(102, 126, 234, 0.1)',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                    transition: 'all 0.3s ease',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    '&:hover': {
                      transform: 'translateY(-8px)',
                      boxShadow: '0 12px 40px rgba(0,0,0,0.15)',
                      border: '1px solid rgba(102, 126, 234, 0.2)'
                    }
                  }}
                >
                  <Typography 
                    variant="h5" 
                    sx={{ 
                      fontWeight: 700, 
                      mb: 2,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent'
                    }}
                  >
                    {step.title}
                  </Typography>
                  <Typography 
                    variant="body1" 
                    color="text.secondary"
                    sx={{ 
                      lineHeight: 1.6,
                      fontSize: '1rem'
                    }}
                  >
                    {step.description}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        </Container>
      </Box>

      {/* Courses Section */}
      <Box id="courses" sx={{ py: { xs: 8, md: 12 }, bgcolor: '#f8fafc' }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography
              variant="h3"
              component="h2"
              sx={{
                fontWeight: 700,
                mb: 2,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              Our Courses
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
              Explore our comprehensive financial education courses designed specifically for Students
            </Typography>
          </Box>

          {/* Desktop: Horizontal layout with conditional arrows */}
          {isLargeScreen ? (
            <Box sx={{ position: 'relative' }}>
              {/* Left Arrow - Only show if there are more cards than can fit */}
              {courses.length > 4 && (
                <IconButton
                  onClick={() => scrollCourses('left')}
                  disabled={currentCourseIndex === 0}
                  sx={{
                    position: 'absolute',
                    left: -20,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    zIndex: 2,
                    bgcolor: 'white',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                    '&:hover': {
                      bgcolor: 'grey.50',
                      transform: 'translateY(-50%) scale(1.1)'
                    },
                    '&:disabled': {
                      opacity: 0.3
                    }
                  }}
                >
                  <ChevronLeftIcon />
                </IconButton>
              )}

              {/* Right Arrow - Only show if there are more cards than can fit */}
              {courses.length > 4 && (
                <IconButton
                  onClick={() => scrollCourses('right')}
                  disabled={currentCourseIndex >= courses.length - 3}
                  sx={{
                    position: 'absolute',
                    right: -20,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    zIndex: 2,
                    bgcolor: 'white',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                    '&:hover': {
                      bgcolor: 'grey.50',
                      transform: 'translateY(-50%) scale(1.1)'
                    },
                    '&:disabled': {
                      opacity: 0.3
                    }
                  }}
                >
                  <ChevronRightIcon />
                </IconButton>
              )}

              {/* Container - Show all cards if 4 or fewer, otherwise scrollable */}
              <Box
                ref={coursesScrollRef}
                onWheel={courses.length > 4 ? handleWheelScroll : undefined}
                sx={{
                  display: 'flex',
                  gap: 3,
                  overflowX: courses.length > 4 ? 'hidden' : 'visible',
                  scrollBehavior: 'smooth',
                  justifyContent: courses.length <= 4 ? 'center' : 'flex-start',
                  '&::-webkit-scrollbar': {
                    display: 'none'
                  },
                  scrollbarWidth: 'none'
                }}
              >
                {courses.map((course, index) => (
                  <Card
                    key={index}
                    sx={{
                      width: '260px',
                      height: '240px',
                      display: 'flex',
                      flexDirection: 'column',
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(248,250,252,0.9) 100%)',
                      border: '1px solid rgba(102, 126, 234, 0.1)',
                      boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                      transition: 'all 0.3s ease',
                      cursor: 'pointer',
                      flexShrink: 0,
                      '&:hover': {
                        transform: 'translateY(-6px)',
                        boxShadow: '0 12px 40px rgba(0,0,0,0.15)',
                        border: `1px solid ${course.color}20`,
                        '& .course-arrow': {
                          transform: 'translateX(4px)',
                          color: course.color
                        }
                      }
                    }}
                  >
                    <CardContent sx={{ p: 2, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                      <Box sx={{ textAlign: 'center', mb: 1.5 }}>
                        <Typography
                          variant="h2"
                          sx={{
                            fontSize: '2rem',
                            mb: 1,
                            display: 'block'
                          }}
                        >
                          {course.emoji}
                        </Typography>
                        <Typography
                          variant="h6"
                          component="h3"
                          sx={{
                            fontWeight: 700,
                            mb: 1,
                            color: course.color,
                            fontSize: '1rem'
                          }}
                        >
                          {course.title}
                        </Typography>
                      </Box>
                      
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          lineHeight: 1.4,
                          fontSize: '0.85rem',
                          flexGrow: 1,
                          mb: 1.5,
                          wordWrap: 'break-word',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical'
                        }}
                      >
                        {course.description}
                      </Typography>

                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: course.color,
                          fontWeight: 600,
                          fontSize: '0.8rem',
                          transition: 'all 0.3s ease'
                        }}
                        className="course-arrow"
                      >
                        Learn More
                        <ArrowIcon sx={{ ml: 0.5, fontSize: '0.9rem' }} />
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            </Box>
          ) : (
            /* Mobile/Tablet: Grid layout */
            <Grid container spacing={3}>
              {courses.map((course, index) => (
                <Grid item xs={12} sm={6} key={index}>
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(248,250,252,0.9) 100%)',
                      border: '1px solid rgba(102, 126, 234, 0.1)',
                      boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                      transition: 'all 0.3s ease',
                      cursor: 'pointer',
                      minHeight: '220px',
                      '&:hover': {
                        transform: 'translateY(-6px)',
                        boxShadow: '0 12px 40px rgba(0,0,0,0.15)',
                        border: `1px solid ${course.color}20`,
                        '& .course-arrow': {
                          transform: 'translateX(4px)',
                          color: course.color
                        }
                      }
                    }}
                  >
                    <CardContent sx={{ p: 2, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                      <Box sx={{ textAlign: 'center', mb: 1.5 }}>
                        <Typography
                          variant="h2"
                          sx={{
                            fontSize: '2rem',
                            mb: 1,
                            display: 'block'
                          }}
                        >
                          {course.emoji}
                        </Typography>
                        <Typography
                          variant="h6"
                          component="h3"
                          sx={{
                            fontWeight: 700,
                            mb: 1,
                            color: course.color,
                            fontSize: '1rem'
                          }}
                        >
                          {course.title}
                        </Typography>
                      </Box>
                      
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          lineHeight: 1.4,
                          fontSize: '0.85rem',
                          flexGrow: 1,
                          mb: 1.5
                        }}
                      >
                        {course.description}
                      </Typography>

                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: course.color,
                          fontWeight: 600,
                          fontSize: '0.8rem',
                          transition: 'all 0.3s ease'
                        }}
                        className="course-arrow"
                      >
                        Learn More
                        <ArrowIcon sx={{ ml: 0.5, fontSize: '0.9rem' }} />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Container>
      </Box>

      {/* Testimonials Section */}
      <Box id="testimonials" sx={{ py: { xs: 8, md: 12 }, bgcolor: 'white' }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography
              variant="h3"
              component="h2"
              sx={{
                fontWeight: 700,
                mb: 2,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              What Our Users Say
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
              Join thousands of students and professionals who have transformed their financial lives
            </Typography>
          </Box>

          <Box sx={{ 
            display: 'flex', 
            gap: 3, 
            overflowX: 'auto',
            pb: 2,
            '&::-webkit-scrollbar': {
              height: '8px',
            },
            '&::-webkit-scrollbar-track': {
              background: '#f1f1f1',
              borderRadius: '4px',
            },
            '&::-webkit-scrollbar-thumb': {
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '4px',
            },
            '&::-webkit-scrollbar-thumb:hover': {
              background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
            }
          }}>
            {testimonials.map((testimonial, index) => (
              <Card 
                key={index}
                sx={{ 
                  minWidth: '350px',
                  maxWidth: '400px',
                  p: 4, 
                  height: '280px',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: '0 12px 40px rgba(0,0,0,0.15)'
                  }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <Avatar sx={{ 
                    width: 56, 
                    height: 56, 
                    fontSize: '2rem', 
                    mr: 2,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                  }}>
                    {testimonial.avatar}
                  </Avatar>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {testimonial.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {testimonial.role}
                    </Typography>
                  </Box>
                </Box>
                <Typography 
                  variant="body1" 
                  sx={{ 
                    mb: 3, 
                    fontStyle: 'italic',
                    flex: '1',
                    lineHeight: 1.6,
                    color: 'text.primary'
                  }}
                >
                  "{testimonial.content}"
                </Typography>
                <Box sx={{ display: 'flex', mt: 'auto' }}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <StarIcon 
                      key={star} 
                      sx={{ 
                        color: '#ffd700', 
                        fontSize: 20,
                        mr: 0.5
                      }} 
                    />
                  ))}
                </Box>
              </Card>
            ))}
          </Box>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box
        sx={{
          py: { xs: 8, md: 12 },
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          textAlign: 'center'
        }}
      >
        <Container maxWidth="md">
          <Typography variant="h3" sx={{ fontWeight: 700, mb: 3 }}>
            Ready to Master Your Money?
          </Typography>
          <Typography variant="h6" sx={{ mb: 4, opacity: 0.9 }}>
            Join thousands of students and professionals who are already building better financial futures
          </Typography>
          <Button
            variant="contained"
            size="large"
            onClick={onGetStarted}
            sx={{
              bgcolor: 'white',
              color: '#667eea',
              px: 6,
              py: 2,
              fontSize: '1.2rem',
              fontWeight: 600,
              '&:hover': {
                bgcolor: '#f8f9fa',
                transform: 'translateY(-2px)',
                boxShadow: '0 8px 25px rgba(0,0,0,0.15)'
              },
              transition: 'all 0.3s ease'
            }}
          >
            Start Your Free Journey
            <ArrowIcon sx={{ ml: 1 }} />
          </Button>
        </Container>
      </Box>
    </Box>
  );
}; 