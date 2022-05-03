pipeline {
  agent {
    docker {
      image 'python:3.8'
    }
  }
  stages {
    stage('Create Virtual Environment') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -e mirrulations-client
          pip install -e mirrulations-core
          pip install -e mirrulations-dashboard
          pip install -e mirrulations-mocks
          pip install -e mirrulations-work-generator
          pip install -e mirrulations-work-server
          pip install -e mirrulations-validation
        '''
      }
    }

    stage('Unit Tests') {
      steps {
        sh '''
          . .venv/bin/activate
          make test
        '''
      }
    }
    stage('Static Analysis') {
      steps {
        sh '''
          . .venv/bin/activate
          make static
        '''
      }
    }
  }
}
